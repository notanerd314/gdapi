from .helpers import *
from .exceptions import *
from .models.level import *
from .models.song import *
from .models.users import *
from datetime import timedelta
from typing import Union, Tuple

_secret = "Wmfd2893gb7"

# TODO: Add filter for lists.
# TODO: Organize methods into subclasses or something I don't even fucking know?
# TODO: fuck my sanity

class Client:
    """
    Client for interacting with Geometry Dash.

    You can use it to download levels, get music library, load profiles, etc. Signing in accounts will be added in v2.0.

    Example usage:
    ```
    >>> gd = Client()
    >>> level = gd.search_level("sigma") # Returns a list of LevelDisplay instances
    [LevelDisplay(id=51657783, name='Sigma', description='Sigma', downloads=582753, likes=19492, ...), ...]
    ```
    """
    def __init__(self) -> None:
        pass

    async def download_level(self, id: int) -> Level:
        """
        Downloads a specific level from the Geometry Dash servers using the provided ID.
        
        :param id: The ID of the level.
        :type id: int
        :return: A `Level` instance containing the downloaded level data.
        """
        if not isinstance(id, int):
            raise ValueError("ID must be an int.")

        response = await send_post_request(
            url="http://www.boomlings.com/database/downloadGJLevel22.php", 
            data={"levelID": id, "secret": _secret}
        )

        # Check if response is valid
        check_negative_1_response(response, InvalidLevelID, f"Invalid level ID {id}.")

        return Level.from_raw(response)

    async def download_daily_level(self, return_weekly: bool = False, get_time_left: bool = False) -> Union[Level, Tuple[Level, timedelta]]:
        """
        Downloads the daily or weekly level from the Geometry Dash servers. You can return the time left for the level optionally.

        If `get_time_left` is set to True then returns a tuple containing the `Level` and the time left for the level.

        :param return_weekly: Whether to return the weekly or daily level. Defaults to False for daily.
        :type return_weekly: bool
        :param get_time_left: Whether to return both the level and the time left for the level. Defaults to False.
        :type get_time_left: bool
        :return: A `Level` instance containing the downloaded level data.
        """
        level = await self.download_level(-2 if return_weekly else -1)
        
        # Makes another response for time left.
        if get_time_left:
            daily_data: str = await send_post_request(
                url="http://www.boomlings.com/database/getGJDailyLevel.php", 
                data={"secret": _secret, "weekly": "1" if return_weekly else "0"}
            )
            check_negative_1_response(daily_data, ResponseError, "Cannot get current time left for the daily/weekly level.")
            daily_data = daily_data.split("|")
            return level, timedelta(seconds=int(daily_data[1]))

        return level

    async def search_levels(
        self, query: str = "", page: int = 0, 
        level_rating: LevelRating = None, length: Length = None,
        difficulty: List[Difficulty] = None, demon_difficulty: DemonDifficulty = None,
        two_player_mode: bool = False, has_coins: bool = False, not_copied: bool = False,
        song_id: int = None, gd_world: bool = False, sort: Sort = 0
    ) -> List[LevelDisplay]:
        """
        Searches for levels matching the given query string and filters them.

        To get a specific demon difficulty, make param `difficulty` as `Difficulty.DEMON`.

        **Note: `difficulty`, `length` and `query` does not work with `sort`!**

        :param query: The query for the search.
        :type query: Optional[str]
        :param page: The page number for the search. Defaults to 0.
        :type page: int
        :param level_rating: The level rating filter. (Featured, Epic, Legendary, ...)
        :type level_rating: Optional[LevelRating]
        :param length: The length filter.
        :type length: Optional[Length]
        :param difficulty: The difficulty filter.
        :type difficulty: Optional[List[Difficulty]]
        :param demon_difficulty: The demon difficulty filter.
        :type demon_difficulty: Optional[DemonDifficulty]
        :param two_player_mode: Filters level that has two player mode enabled.
        :type two_player_mode: Optional[bool]
        :param has_coins: Filters level that has coins.
        :type has_coins: Optional[bool]
        :param not_copied: Filters level that has not been copied.
        :type not_copied: Optional[bool]
        :param song_id: Filters level that has the specified song ID.
        :type song_id: Optional[int]
        :param gd_world: Filters level that is from Geometry Dash World.
        :type gd_world: Optional[bool]
        :param sort: Sort the result by Magic, Recent, ...
        :type sort: Optional[Union[Sort, str]]

        :return: A list of `LevelDisplay` instances.
        """
        
        # Standard data
        data = {
            "secret": _secret,
            "type": sort.value if isinstance(sort, Sort) else sort,
            "page": page,
        }
        
        # Level rating check
        if level_rating:
            match level_rating:
                case LevelRating.NO_RATE: data["noStar"] = 1
                case LevelRating.RATED: data["star"] = 1
                case LevelRating.FEATURED: data["featured"] = 1
                case LevelRating.EPIC: data["epic"] = 1
                case LevelRating.MYTHIC: data["legendary"] = 1
                case LevelRating.LEGENDARY: data["mythic"] = 1
                case _: raise ValueError("Invalid level rating, are you sure that it's a LevelRating object?")

        # Difficulty and demon difficulty checks
        if difficulty:
            if Difficulty.DEMON in difficulty and len(difficulty) > 1:
                raise ValueError("Difficulty.DEMON cannot be combined with other difficulties!")
            data["diff"] = ",".join(str(determine_search_difficulty(diff)) for diff in difficulty)

        if demon_difficulty:
            if difficulty != [Difficulty.DEMON]:
                raise ValueError("Demon difficulty can only be used with Difficulty.DEMON!")
            data["demonFilter"] = determine_demon_search_difficulty(demon_difficulty)

        # Optional parameters
        if song_id:
            data.update({"customSong": 1, "song": song_id})

        optional_params = {
            "length": length.value if length else None,
            "twoPlayer": int(two_player_mode) if two_player_mode else None,
            "coins": int(has_coins) if has_coins else None,
            "original": int(not_copied) if not_copied else None,
            "gdw": int(gd_world) if gd_world else None,
            "str": query if query else None
        }

        # Update data with non-None values from optional_params
        data.update({k: v for k, v in optional_params.items() if v is not None})

        # Do the response
        search_data: str = await send_post_request(url="http://www.boomlings.com/database/getGJLevels21.php", data=data)
        
        check_negative_1_response(search_data, SearchLevelError, "Unable to fetch search results. Perhaps it doesn't exist after all?")

        parsed_results = parse_search_results(search_data)
        return [LevelDisplay.from_dict(result) for result in parsed_results]

    async def get_music_library(self) -> MusicLibrary:
        """
        Gets the current music library in RobTop's servers.

        :return: A `MusicLibrary` instance containing all the music library data.
        """
        response = await send_get_request(
            url="https://geometrydashfiles.b-cdn.net/music/musiclibrary_02.dat",
        )
        music_library_encoded = response.content
        music_library = decrypt_data(music_library_encoded, "base64_decompress")
        return MusicLibrary.from_raw(music_library)
    
    async def get_sfx_library(self) -> SFXLibrary:
        """
        Gets the current SFX library in RobTop's servers.

        :return: A `SFXLibrary` instance containing all the SFX library data.
        """
        response = await send_get_request(
            url="https://geometrydashfiles.b-cdn.net/sfx/sfxlibrary.dat",
        )
        music_library_encoded = response.content
        music_library = decrypt_data(music_library_encoded, "base64_decompress")
        return SFXLibrary.from_raw(music_library)

    async def get_song_data(self, id: int) -> Song:
        """
        Gets song data by ID, either from Newgrounds or the music library.

        :param id: The ID of the song. (Use ID larger than 10000000 to get the song from the library.)
        :type id: int
        :return: A `Song` instance containing the song data.
        """
        response = await send_post_request(
            url="http://www.boomlings.com/database/getGJSongInfo.php",
            data={'secret': _secret, "songID": id}
        )
        check_negative_1_response(response, InvalidSongID, f"Invalid song ID {id}.")
        return Song.from_raw(response)

    async def get_user_profile(self, account_id: int) -> UserProfile:
        """
        Get an user profile by account ID.

        :param account_id: The account ID to retrieve the profile.
        :type account_id: int
        :return: A `UserProfile` instance containing the user's profile data.
        """
        if not isinstance(account_id, int):
            raise ValueError("ID must be int")
        
        url = "http://www.boomlings.com/database/getGJUserInfo20.php"
        data = {'secret': _secret, "targetAccountID": account_id}

        response = await send_post_request(url=url, data=data)
        check_negative_1_response(response, InvalidAccountID, f"Invalid account ID {account_id}.")
        return UserProfile.from_raw(response)

    async def search_user(self, username: str) -> UserProfile:
        """
        Search for an user by their username. 
        
        **Note:** This method doesn't return the full information, use `UserProfile.reload()` to get the full profile after retrieving.

        :param username: The username to search for.
        :type username: str
        :return: A `UserProfile` instance containing the user's profile data.
        """
        response = await send_post_request(
            url="http://www.boomlings.com/database/getGJUsers20.php",
            data={'secret': _secret, "str": username}
        )
        check_negative_1_response(response, InvalidAccountName, f"Invalid username {username}.")
        return UserProfile.from_raw(response)
    
    async def get_level_comments(self, level_id: int, page: int = 0) -> List[LevelComment]:
        """
        Get level's comments by level ID.

        :param level_id: The ID of the level.
        :type level_id: int
        :param page: The page number for pagination. Defaults to 0.
        :type page: int
        :return: A list of `LevelComment` instances.
        """
        if page < 0:
            raise ValueError("Page number must be non-negative.")
        
        response = await send_post_request(
            url="http://www.boomlings.com/database/getGJComments21.php",
            data={'secret': _secret, "levelID": level_id, "page": page}
        )
        check_negative_1_response(response, InvalidLevelID, f"Invalid level ID {level_id}.")
        return [LevelComment.from_raw(comment_data) for comment_data in response.split("|")]
    
    async def get_user_posts(self, account_id: int, page: int = 0) -> Union[List[UserPost], None]:
        """
        Get an user's posts by Account ID.

        :param account_id: The account ID to retrieve the posts.
        :type account_id: int
        :param page: The page number for pagination. Defaults to 0.
        :type page: int
        :return: A list of `UserPost` instances or None if there are no posts.
        """
        response = await send_post_request(
            url="http://www.boomlings.com/database/getGJAccountComments20.php",
            data={'secret': _secret, "accountID": account_id, "page": page}
        )

        check_negative_1_response(response, ResponseError, "Invalid account ID.")
        if not response.split("#")[0]:
            return None

        posts_list = []
        parsed_res = response.split("#")[0]
        parsed_res = response.split("|")
        for post in parsed_res:
            posts_list.append(UserPost.from_raw(post, account_id))
        return posts_list
        
    async def get_user_comments_history(self, player_id: int, page: int = 0, display_most_liked: bool = False) -> Union[List[LevelComment], None]:
        """
        Get an user's comments history.
        
        :param player_id: The player ID to retrieve the comments history.
        :type player_id: int
        :param page: The page number for pagination. Defaults to 0.
        :type page: int
        :param display_most_liked: Whether to display the most liked comments. Defaults to False.
        :type display_most_liked: bool
        :return: A list of `LevelComment` instances or None if no comments were found.
        """
        response = await send_post_request(
            url="http://www.boomlings.com/database/getGJCommentHistory.php",
            data={'secret': _secret, "userID": player_id, "page": page, "mode": int(display_most_liked)}
        )
        check_negative_1_response(response, ResponseError, "Invalid account ID.")
        if not response.split("#")[0]:
            return None
        
        return [LevelComment.from_raw(comment_data) for comment_data in response.split("#")[0].split("|")]

    async def get_map_packs(self, page: int = 0) -> List[MapPack]:
        """
        Get the full list of map packs available (in a specific page).

        :return: A list of `MapPack` instances.
        """
        if page < 0:
            raise ValueError("Page must be a non-negative number.")
        elif page > 6:
            raise ValueError("Page limit is 6.")
        
        response = await send_post_request(
            url="http://www.boomlings.com/database/getGJMapPacks21.php",
            data={'secret': _secret, 'page': page}
        )
        check_negative_1_response(response, LoadError, "An error occurred when getting map packs.")
        map_packs = response.split('#')[0].split("|")
        return [MapPack.from_raw(map_pack_data) for map_pack_data in map_packs]

    async def get_gauntlets(self, only_2_point_1: bool = True, add_ncs_gauntlets: bool = True) -> List[Gauntlet]:
        """
        Get the list of gauntlets objects.

        :param only_2_point_1: Whether to get ONLY the 2.1 guantlets or both 2.2 and 2.1. Defaults to True.
        :type only_2_point_1: bool
        :param add_ncs_gauntlets: Whether to add NCS gauntlets to the list. Defaults to True.
        :type add_ncs_gauntlets: bool
        :return: A list of `Gauntlet` instances.
        """
        response = await send_post_request(
            url="http://www.boomlings.com/database/getGJGauntlets21.php",
            data={'secret': _secret, 'special': int(only_2_point_1)}
        )
        check_negative_1_response(response, LoadError, "An error occurred when getting gauntlets.")
        guantlets = response.split('#')[0].split("|")
        list_guantlets = [Gauntlet.from_raw(guantlet) for guantlet in guantlets]

        if add_ncs_gauntlets:
            list_guantlets.append(Gauntlet(id=51, name="NCS I", levels_id=[110715909, 110774313, 110665441, 110610038, 109432148], image_url="https://gdbrowser.com/assets/gauntlets/ncs_i.png"))
            list_guantlets.append(Gauntlet(id=52, name="NCS II", levels_id=[110681124, 110774310, 110638716, 110473393, 110774330], image_url="https://gdbrowser.com/assets/gauntlets/ncs_ii.png"))

        return list_guantlets
    
    async def search_lists(self, query: str) -> List[LevelList]:
        """
        Search for level lists by query.

        :param query: The query string to search for.
        :type query: str
        :return: A list of `LevelList` instances.
        """
        response = await send_post_request(
            url="http://www.boomlings.com/database/getGJLevelLists.php",
            data={'secret': _secret, 'str': query, 'type': 0}
        )
        check_negative_1_response(response, SearchLevelError, "An error occurred while searching lists, maybe it doesn't exist?")
        response = response.split("#")[0]
        return [LevelList.from_raw(level_list_data) for level_list_data in response.split("|")]