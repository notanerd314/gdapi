"""
# .helpers

A module containing all helper functions for the module.

You typically don't want to use this module because it has limited documentation and confusing information.
"""

import httpx
import base64
import zlib
import re
from typing import List, Dict, Union
from .models.enums import Difficulty, DemonDifficulty
from .exceptions import *

# Helper function to send an asynchronous POST request
async def send_post_request(**kwargs) -> str:
    """Send an asynchronous POST request and handle response. Returns the content of the response."""
    async with httpx.AsyncClient() as client:
        response = await client.post(**kwargs, headers={"User-Agent": ""})
        if response.status_code == 200:
            return response.text
        else:
            raise ResponseError(f"Unable to fetch data, got {response.status_code}.")

async def send_get_request(**kwargs) -> httpx.Response:
    """Send an asynchronous GET request and handle response."""
    async with httpx.AsyncClient() as client:
        response = await client.get(**kwargs, timeout=60)
        if response.status_code == 200:
            return response
        else:
            raise ResponseError(f"Unable to fetch data, got {response.status_code}.")

# Function to add padding to base64 encoded data
def add_padding(data: str) -> str:
    """Add padding to the input base64 data to make its length a multiple of 4.

    Args:
        data (str): The input data to pad.

    Returns:
        str: The padded data.
    """
    if not isinstance(data, str):
        raise ValueError("Input data must be a string.")

    return data + "=" * ((4 - len(data) % 4) % 4)

# XOR decryption function
def xor_decrypt(input_bytes: bytes, key: str) -> str:
    """Decrypt the input bytes using XOR with the provided key."""
    key_bytes = key.encode()
    return ''.join(chr(byte ^ key_bytes[i % len(key_bytes)]) for i, byte in enumerate(input_bytes))

# Decrypt function with multiple methods
def decrypt_data(encrypted: Union[str, bytes], decrypt_type: str = "base64") -> str:
    """Decrypt the input data using the specified decrypt type."""
    if decrypt_type == "base64_decompress":
        padded_data = add_padding(encrypted)
        decoded_data = base64.urlsafe_b64decode(encrypted)
        decompressed_data = zlib.decompress(decoded_data, 15 | 32)
        return decompressed_data.decode()
    elif decrypt_type == "xor":
        decoded_bytes = base64.b64decode(encrypted)
        return xor_decrypt(decoded_bytes, '26364')
    elif decrypt_type == "base64":
        # padded_data = add_padding(encrypted)
        return base64.urlsafe_b64decode(encrypted).decode('utf-8')
    else:
        raise ValueError("Invalid decrypt type!")

# Function to parse key-value pairs from a string
def parse_key_value_pairs(text: str, separator: str = ":") -> Dict[str, Union[str, int]]:
    """Parse key-value pairs from a colon-separated string."""
    try:
        pairs = {}
        text = text.split("#")[0]
        items = text.split(separator)
        for index in range(0, len(items), 2):
            key = items[index]
            value = items[index + 1] if index + 1 < len(items) else None
            if value is not None:
                try:
                    value = int(value)
                except ValueError:
                    pass
            pairs[key] = value
        return pairs
    except Exception as e:
        raise ParseError(f"Error parsing key-value pairs: {str(e)}") from None

# Function to parse level data
def parse_level_data(text: str) -> Dict[str, Union[str, int]]:
    """Parse level data from text."""
    parsed = parse_key_value_pairs(text)
    parsed['4'] = decrypt_data(parsed['4'], 'base64_decompress') if '4' in parsed else None
    parsed['3'] = decrypt_data(parsed['3'])
    
    # Handle special case for '27'
    if '27' not in parsed:
        parsed['27'] = None
    elif parsed['27'] == "0":
        parsed['27'] = False
    elif parsed['27'] == "Aw==":
        parsed['27'] = True
    else:
        parsed['27'] = decrypt_data(parsed['27'])
    
    return parsed

# Function to parse user data
def parse_user_data(text: str) -> Dict[str, Union[str, int]]:
    """Parse user data from text."""
    return parse_key_value_pairs(text)

# Function to parse comments from text
def parse_comments_data(text: str) -> List[Dict[str, Union[str, int]]]:
    """Parse comments from text."""
    items = text.split('|')
    parsed_comments = []
    
    for item in items:
        comment = parse_key_value_pairs(item)
        comment['2'] = decrypt_data(comment['2']) if '2' in comment else None
        parsed_comments.append(comment)
    
    return parsed_comments

# Function to parse song data
def parse_song_data(song: str) -> Dict[str, Union[str, int]]:
    """Parse song data from text."""
    song = song.replace("~", "")
    return parse_key_value_pairs(song, '|')

# Function to parse search results
def parse_search_results(text: str) -> List[Dict[str, Union[Dict, str]]]:
    """Parse search results from input text."""
    try:
        split_parts = text.split('#')
        levels_data = split_parts[0].split("|")
        creators_data = split_parts[1].split("|")
        songs_data = split_parts[2].split("~:~")
        
        parsed_levels = [{"level": level} for level in levels_data]

        for current_level in parsed_levels:
            level_data = parse_level_data(current_level['level'])
            user_id = str(level_data.get('6'))  # Ensure user_id is a string

            # Match creator by looping through creators_data
            matching_creator = None
            for creator in creators_data:
                creator_info = creator.split(":")
                if creator_info[0] == user_id:
                    matching_creator = creator_info
                    break

            if matching_creator:
                current_level['creator'] = {
                    "playerID": matching_creator[0],
                    "playerName": matching_creator[1],
                    "accountID": matching_creator[2]
                }
            else:
                current_level['creator'] = {
                    "playerID": None,
                    "playerName": None,
                    "accountID": None
                }

        for song in songs_data:
            parsed_song = parse_song_data(song)
            for current_level in parsed_levels:
                level_data = parse_level_data(current_level['level'])
                if level_data.get("35") == 0:
                    current_level['song'] = None
                elif level_data['35'] == int(parsed_song.get("1", -1)):
                    current_level['song'] = song
    except Exception as e:
        raise ParseError(f"Error parsing search results: {str(e)}") from None

    return parsed_levels

def is_newgrounds_song(id: int) -> bool:
    return not id >= 10000000

def parse_comma_separated_int_list(key: str) -> List[int]:
    """
    Helper method to parse a comma-separated list of integers.
    
    :param key: A string of numbers seperated by ","
    :type key: str
    :return: List[int]
    """
    try:
        return [int(x) for x in key.split(",") if x.isdigit()]
    except AttributeError:
        return []
    
def determine_difficulty(parsed: dict, return_demon_diff: bool = True) -> Union[Difficulty, DemonDifficulty]:
    """
    Determines the level's difficulty based on parsed data.
    
    :param parsed: Parsed data from the servers
    :type parsed: dict
    :param return_demon_diff: Whether to return the specific demon difficulty (if applicable)
    :type return_demon_diff: bool
    :return: `Difficulty`
    """

    if return_demon_diff and parsed.get('17', False):
        match parsed.get('43', None):
            case 3: return DemonDifficulty.EASY_DEMON
            case 4: return DemonDifficulty.MEDIUM_DEMON
            case 0: return DemonDifficulty.HARD_DEMON
            case 5: return DemonDifficulty.INSANE_DEMON
            case 6: return DemonDifficulty.EXTREME_DEMON
            case _: raise ValueError(f"{parsed.get('43', None)} is not a valid DemonDifficulty.")
    elif parsed.get("25"):
        return Difficulty.AUTO
    else:
        return Difficulty(parsed.get("9", 0) // 10)
    
def determine_list_difficulty(raw_integer_difficulty: int) -> Union[Difficulty, DemonDifficulty]:
    """
    Determines the list's difficulty based on parsed data.
    
    :param raw_integer_difficulty: The number of the difficulty.
    :type raw_integer_difficulty: int
    :return: `Difficulty`
    """

    match raw_integer_difficulty:
        case -1: return Difficulty.NA
        case 0: return Difficulty.AUTO
        case 1: return Difficulty.EASY
        case 2: return Difficulty.NORMAL
        case 3: return Difficulty.HARD
        case 4: return Difficulty.HARDER
        case 5: return Difficulty.INSANE
        case 6: return DemonDifficulty.EASY_DEMON
        case 7: return DemonDifficulty.MEDIUM_DEMON
        case 8: return DemonDifficulty.HARD_DEMON
        case 9: return DemonDifficulty.INSANE_DEMON
        case 10: return DemonDifficulty.EXTREME_DEMON
        case _: raise ValueError(f"Invalid difficulty integer {raw_integer_difficulty}.")

def determine_search_difficulty(difficulty_obj: Difficulty) -> int:
    match difficulty_obj:
        case Difficulty.NA: return -1
        case Difficulty.AUTO: return -3
        case Difficulty.DEMON: return -2
        case Difficulty.EASY: return 1
        case Difficulty.NORMAL: return 2
        case Difficulty.HARD: return 3
        case Difficulty.HARDER: return 4
        case Difficulty.INSANE: return 5
        case _: raise ValueError(f"Invalid difficulty object type {type(difficulty_obj)}")

def determine_demon_search_difficulty(difficulty_obj: DemonDifficulty) -> int:
    match difficulty_obj:
        case DemonDifficulty.EASY_DEMON: return 1
        case DemonDifficulty.MEDIUM_DEMON: return 2
        case DemonDifficulty.HARD_DEMON: return 3
        case DemonDifficulty.INSANE_DEMON: return 4
        case DemonDifficulty.EXTREME_DEMON: return 5
        case _: raise ValueError(f"Invalid demon difficulty object type {type(difficulty_obj)}")