"""
# .helpers

A module containing all helper functions for the module.

You typically don't want to use this module because it has limited documentation and confusing to use.
"""

import aiohttp
import base64
import zlib
import uuid
from typing import List, Dict, Union
from hashlib import sha1
from .entities.enums import Difficulty, DemonDifficulty
from enum import StrEnum
from .exceptions import *

# Constants
XOR_KEY = '26364'
START_ID_SONG_LIB = 10000000
BASE64_PADDING_CHAR = "="
AW_CODE = "Aw=="
DEFAULT_TIMEOUT = 60
UDID_PREFIX = "S"

#* HTTP Helper Functions
async def handle_response(response: aiohttp.ClientResponse) -> aiohttp.ClientResponse:
    response.raise_for_status()
    return response

async def send_post_request(**kwargs) -> str:
    async with aiohttp.ClientSession() as client:
        async with client.post(**kwargs, headers={"User-Agent": ""}) as response:
            response_text = await handle_response(response)
            return await response_text.text()

async def send_get_request(decode: bool = True, **kwargs) -> bytes:
    """Send a GET request and reads the response."""
    client = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(60.0))  # Create session

    response = await client.get(**kwargs)  # Make the GET request
    handled_response = await handle_response(response)  # Handle the response
    response_data = await handled_response.read()
    
    await client.close()  # Close the session

    if decode:
        return response_data.decode()
    else:
        return response_data

#* Encryption and Decryption Functions

class XorKey(StrEnum):
    LEVEL_PASSWORD = "26364"
    GJP = "37526"
    COMMENT = "29481"

class CHKSalt(StrEnum):
    LEVEL = "xI25fpAapCQg"
    COMMENT = "0xPT6iUrtws0J"
    LIKE = "ysg6pUrtjn0J"
    RATE = "ysg6pUrtjn0J"
    PROFILE = "xI35fsAapCRg"
    LEADERBOARD = "yPg6pUrtWn0J"

def uuid4() -> str:
    return str(uuid.uuid4())

def add_padding(data: str) -> str:
    """Add padding to base64-encoded data to make its length a multiple of 4."""
    return data + '=' * ((4 - len(data) % 4) % 4)

def xor(input_bytes: bytes, key: str) -> str:
    key_bytes = key.encode()
    return ''.join(chr(byte ^ key_bytes[i % len(key_bytes)]) for i, byte in enumerate(input_bytes))

def decrypt_data(encrypted: Union[str, bytes], decrypt_type: str = "base64", xor_key: str = None) -> Union[str, None]:
    if not encrypted:
        return None

    if decrypt_type == "base64_decompress":
        decoded_data = base64.urlsafe_b64decode(add_padding(encrypted))
        return zlib.decompress(decoded_data, 15 | 32).decode()
    elif decrypt_type == "xor":
        return xor(base64.b64decode(encrypted), xor_key)
    elif decrypt_type == "base64":
        return base64.urlsafe_b64decode(add_padding(encrypted)).decode()
    else:
        raise ValueError("Invalid decrypt type!")

def generate_chk(values: List[Union[int, str]] = [], key: str = "", salt: str = "") -> str:
    values.append(salt)
    combined_str = ''.join(map(str, values))
    hashed = sha1(combined_str.encode()).hexdigest()
    xored = xor(hashed.encode(), key)
    return base64.urlsafe_b64encode(xored.encode()).decode()


#* Parsing Functions
def parse_key_value_pairs(text: str, separator: str = ":") -> Dict[str, Union[str, int, None]]:
    """
    Parse key-value pairs from a separator-separated string. Example:

    ```
    1:25:2:65:3:okay
    ```

    The first column of the string is the key name, then the next column is the previous key's value then it repeats like a pattern.

    :param text: The string to parse.
    :type text: str
    :param separator: The separator to parse the string (Default is `:`)
    :type separator: str
    :return: A dictionary containing the parsed key-value pairs.
    """
    pairs = {}
    # Parse key-valye pairs
    for index in range(0, len(items := text.split(separator)), 2):
        key, value = items[index], items[index + 1] if index + 1 < len(items) else None

        # Automatically convert str to int if applicable
        pairs[key] = int(value) if value and value.isdigit() else value

    return pairs

def unparse_key_value_pairs(parsed: Dict[str, Union[str, int]], separator: str = ":") -> str:
    """
    Unparse key-value pairs into a separator-separated string. Basically `parse_key_value_pairs` but reversed.
    
    :param parsed: The dictionary containing the parsed key-value pairs.
    :type parsed: Dict[str, Union[str, int]]
    :param separator: The separator to unparse the string.
    :type separator: str
    :return: A string containing the unparsed key-value pairs.
    """

    # Unparse the parsed
    return separator.join(f"{key}{separator}{value}" for key, value in parsed.items())

def parse_level_data(text: str) -> Dict[str, Union[str, int]]:
    # Parsing the data
    parsed = parse_key_value_pairs(text)

    # Decrypt specific values
    parsed['4'] = decrypt_data(parsed.get('4'), 'base64_decompress')
    parsed['3'] = decrypt_data(parsed.get('3'))
    parsed['27'] = decrypt_data(parsed.get('27')) if parsed.get('27') not in [None, "0"] else None

    return parsed

def parse_search_results(text: str) -> List[Dict[str, Union[Dict, str]]]:
    # Split the text into individual level data, creator data, and song data.
    levels_data, creators_data, songs_data = (
        text.split('#')[0].split("|"),
        text.split('#')[1].split("|"),
        text.split('#')[2].split("~:~")
    )
    
    # Parse each level data, creator data, and song data separately and add them to the parsed_levels list.
    parsed_levels = [{"level": parse_level_data(level)} for level in levels_data]

    # Match each level's creator data
    for current_level in parsed_levels:
        level_data = current_level['level']
        user_id = str(level_data.get('6'))  # User ID from level data
        creator_info = next(
            (creator.split(":") for creator in creators_data if creator.startswith(user_id)),
            None
        )
        
        # Add creator information if available
        current_level['creator'] = {
            "playerID": creator_info[0] if creator_info else None,
            "playerName": creator_info[1] if creator_info else None,
            "accountID": int(creator_info[2]) if creator_info else None
        }
    
    # Match each level's song data
    for song in songs_data:
        parsed_song = parse_song_data(song)

        # Connect the song to the correct level
        for current_level in parsed_levels:
            level_data = current_level['level']
            if level_data.get("35") == 0:
                current_level['song'] = None
            elif level_data.get("35") == int(parsed_song.get("1", -1)):
                current_level['song'] = parsed_song

    return parsed_levels

def parse_user_data(text: str) -> Dict[str, Union[str, int]]:
    # Literally parse_key_value_pairs lol
    return parse_key_value_pairs(text)

def parse_comments_data(text: str) -> List[Dict[str, Union[str, int]]]:
    # Parsing multiple comments, not 1 comment.
    items = text.split('|')
    return [{"comment": parse_key_value_pairs(item)} for item in items]

def parse_song_data(song: str) -> Dict[str, Union[str, int]]:
    # Literally parse_key_value_pairs again lol
    return parse_key_value_pairs(song.replace("~", ""), '|')

# Difficulty Determination
_DIFFICULTY_ = {
    -1: Difficulty.NA, 0: Difficulty.AUTO, 1: Difficulty.EASY, 2: Difficulty.NORMAL, 3: Difficulty.HARD,
    4: Difficulty.HARDER, 5: Difficulty.INSANE, 6: DemonDifficulty.EASY_DEMON, 7: DemonDifficulty.MEDIUM_DEMON,
    8: DemonDifficulty.HARD_DEMON, 9: DemonDifficulty.INSANE_DEMON, 10: DemonDifficulty.EXTREME_DEMON
}
"""Difficulty mapping but kinda useless don't you think?"""

def determine_difficulty(parsed: dict, return_demon_diff: bool = True) -> Union[Difficulty, DemonDifficulty]:
    """
    Determines the level's difficulty based on parsed data.
    
    Args:
        parsed (dict): Parsed data from the server.
        return_demon_diff (bool): Whether to return specific demon difficulty (if applicable).

    Returns:
        Union[Difficulty, DemonDifficulty]: Difficulty level or specific demon difficulty.
    """
    if return_demon_diff and parsed.get('17', False):
        # If it's a demon
        match parsed.get('43'):
            case 3: return DemonDifficulty.EASY_DEMON
            case 4: return DemonDifficulty.MEDIUM_DEMON
            case 0: return DemonDifficulty.HARD_DEMON
            case 5: return DemonDifficulty.INSANE_DEMON
            case 6: return DemonDifficulty.EXTREME_DEMON
            case _: raise ValueError(f"Invalid DemonDifficulty: {parsed.get('43')}")
    elif parsed.get("25"):
        # Return AUTO if auto
        return Difficulty.AUTO
    else:
        # If not, return the normal difficulties
        return Difficulty(parsed.get("9", 0) // 10)

def determine_search_difficulty(difficulty_obj: Difficulty) -> int:
    """
    Converts a Difficulty object to its corresponding integer value for search purposes.
    
    Args:
        difficulty_obj (Difficulty): The difficulty object.

    Returns:
        int: Integer representing the search difficulty.
    """
    _DIFFICULTY_ = {
        Difficulty.NA: -1,
        Difficulty.AUTO: -3,
        Difficulty.DEMON: -2,
        Difficulty.EASY: 1,
        Difficulty.NORMAL: 2,
        Difficulty.HARD: 3,
        Difficulty.HARDER: 4,
        Difficulty.INSANE: 5
    }
    
    return _DIFFICULTY_.get(difficulty_obj, -1)

def determine_demon_search_difficulty(difficulty_obj: DemonDifficulty) -> int:
    """Converts a DemonDifficulty object to its corresponding integer value."""

    # Convert the object to an interger value based on the search's enums.
    match difficulty_obj:
        case DemonDifficulty.EASY_DEMON: return 1
        case DemonDifficulty.MEDIUM_DEMON: return 2
        case DemonDifficulty.HARD_DEMON: return 3
        case DemonDifficulty.INSANE_DEMON: return 4
        case DemonDifficulty.EXTREME_DEMON: return 5
        case _: raise ValueError(f"Invalid demon difficulty object type {type(difficulty_obj)}")

def determine_list_difficulty(raw_integer_difficulty: int) -> Union[Difficulty, DemonDifficulty]:
    """
    Converts a raw integer difficulty value to its corresponding Difficulty or DemonDifficulty object.
    """
    return _DIFFICULTY_.get(raw_integer_difficulty, Difficulty.NA)

# Utility Functions
def is_newgrounds(id: int) -> bool:
    """Checks if a song ID is from Newgrounds."""
    return id < START_ID_SONG_LIB

def parse_comma_separated_int_list(key: str) -> List[int]:
    """Split the string by `,` then turn it into a list of integers."""
    try:
        return [int(x) for x in key.split(",") if x.isdigit()]
    except AttributeError:
        return []