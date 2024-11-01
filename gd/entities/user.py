"""
## .models.users
A module containing all the classes and methods related to users and accounts in Geometry Dash.
"""

from ..helpers import *
from .enums import *
from .cosmetics import *
from .level import Comment, LevelDisplay
from typing import List, Optional, Union
from dataclasses import dataclass
from .entity import Entity

_secret = "Wmfd2893gb7"

@dataclass
class UserPost:
    """
    A class representing a post from an account.

    Attributes
    ----------
    content : str
        The content of the post.
    likes : int
        The number of likes of the post.
    post_id : int
        The id of the post.
    posted_ago : str
        The time when the post was posted in a string, example: `"5 months"`
    author_account_id : Union[int, None]
        The ID of the author, or None if doesn't exist.
    """
    content: str = None
    likes: int = None
    post_id: int = None
    posted_ago: str = None
    author_account_id: Union[int, None] = None

    @staticmethod
    def from_raw(raw_str: str, account_id: int = None) -> 'UserPost':
        """
        A static method that converts the raw data from the server into a UserPost instance.

        :param raw_str: The raw data from the server.
        :type raw_str: str
        :param account_id: The account ID of the user, optional if not provided.
        :type account_id: Union[int, None]
        :return: A UserPost instance.
        """
        parsed = raw_str.split(":")
        comment_value = parse_key_value_pairs(parsed[0], '~')

        try:
            return UserPost(
                content=decrypt_data(comment_value.get("2", "")),
                likes=int(comment_value.get("4", 0)),
                post_id=int(comment_value.get("6", 0)),
                posted_ago=comment_value.get("9", None),
                author_account_id=account_id
            )
        except Exception as e:
            raise ParseError(f"Failed to parse the data provided, error: {e}")

@dataclass
class UserProfile(Entity):
    """
    A class representing an user's profile.
    
    Attributes
    ----------
    name : str
        The name of the user.
    player_id : int
        The player ID of the user.
    account_id : int
        The account ID of the user.
    stars : int
        The amount of stars the user has.
    moons : int
        The amount of moons the user has.
    demons : int
        The amount of demons the user has beaten.
    diamonds : int
        The amount of diamonds the user has.
    rank : int
        The rank of the user in the leaderboard.
    creator_points : int
        The amount of creator points the user has.
    secret_coins : int
        The amount of secret coins the user has.
    user_coins : int
        The amount of user coins the user has.
    registered : bool
        If the user has registered.
    mod_level : Optional[ModRank]
        The mod level of the user.
    primary_color_id : Optional[Color_id]
        The primary color_id of the user's icon.
    secondary_color_id : Optional[Color_id]
        The secondary color_id of the user's icon.
    glow_color_id : Optional[Color_id]
        The glow color_id of the user's icon.
    profile_icon_type : Optional[Gamemode]
        The gamemode that the user primarily chooses to display.
    youtube : Union[str, None]
        The YouTube channel link of the user.
    twitter_or_x : Union[str, None]
        The Twitter (or X) username of the user.
    twitch : Union[str, None]
        The Twitch username of the user.
    """
    name: str = None
    player_id: int = None
    account_id: int = None
    stars: Optional[int] = None
    moons: Optional[int] = None
    demons: Optional[int] = None
    diamonds: Optional[int] = None
    rank: Optional[int] = None
    creator_points: Optional[int] = None
    secret_coins: Optional[int] = None
    user_coins: Optional[int] = None
    registered: Optional[bool] = None
    mod_level: Optional[ModRank] = None

    primary_color_id: Optional[int] = None
    secondary_color_id: Optional[int] = None
    glow_color_id: Optional[int] = None
    profile_icon_type: Optional[Gamemode] = None
    
    youtube: Optional[str] = None
    twitter: Optional[str] = None
    """i ain't calling it x"""
    twitch: Optional[str] = None

    @staticmethod
    def from_raw(raw_str: str) -> 'UserProfile':
        """
        Parse the string data from the servers and returns an UserProfile instance.

        :param raw_str: The raw data from the server.
        :type raw_str: str
        :return: An instance of the UserProfile class.                                     
        """
        parsed = parse_key_value_pairs(raw_str)
        try:
            return UserProfile(
                name=parsed.get('1', None),
                player_id=parsed.get('2', 0),
                account_id=parsed.get('16', 0),
                stars=parsed.get('3', 0),
                moons=parsed.get('52', 0),
                demons=parsed.get('4', 0),
                diamonds=parsed.get('46'),
                rank=parsed.get('30'),
                creator_points=parsed.get('8', 0),
                secret_coins=parsed.get('13', 0),
                user_coins=parsed.get('17', 0),
                registered=True if parsed.get('29') == 1 else False,
                mod_level=ModRank(parsed.get('49', 0)),

                profile_icon_type=Gamemode(parsed.get('14', 1)),
                primary_color_id=int(parsed.get('10', 0)),
                secondary_color_id=int(parsed.get('11', 0)),
                glow_color_id=int(parsed.get('51')) if parsed.get('51', None) is not None else None,

                youtube=parsed.get('20', None) if parsed.get('20') != r"%%00" else None,
                twitter=parsed.get('44'),
                twitch=parsed.get('45')
            )
        except Exception as e:
            raise ParseError(f"Could not parse the data provided, error: {e}")

    async def posts(self, page: int = 0) -> List[UserPost] | None:
        """
        Load all posts from the user.

        :param page: The page number to load, default is 0.
        :type page: int
        :return: A list of UserPost instances or None if the request failed.
        """
        response = await send_post_request(
            url="http://www.boomlings.com/database/getGJAccountComments20.php",
            data={'secret': _secret, "accountID": self.account_id, "page": page}
        )

        check_errors(response, LoadError, f"Something wrong had happened when fetching the user's posts.")
        if not response.split("#")[0]:
            return None

        posts_list = []
        parsed_res = response.split("#")[0]
        parsed_res = response.split("|")
        for post in parsed_res:
            posts_list.append(UserPost.from_raw(post, self.account_id))
        return posts_list
        
    async def comments(self, page: int = 0, display_most_liked: bool = False) -> List[Comment]:
        """
        Get user's comments history.

        :param page: The page number to load, default is 0.
        :type page: int
        :param display_most_liked: If True, display most liked comments, otherwise display newest comments.
        :type display_most_liked: bool
        :return: A list of Comment instances.
        """
        response = await send_post_request(
            url="http://www.boomlings.com/database/getGJCommentHistory.php",
            data={'secret': _secret, "userID": self.player_id, "page": page, "mode": int(display_most_liked)}
        )
        check_errors(response, LoadError, f"Something wrong had happened when fetching the user's comments.")
        if not response.split("#")[0]:
            return None
        
        return [Comment.from_raw(comment_data) for comment_data in response.split("#")[0].split("|")]

    async def levels(self, page: int = 0) -> List[LevelDisplay]:
        """
        Get user's levels.

        :param page: The page number to load, default is 0.
        :type page: int
        :return: A list of LevelDisplay instances.
        """

        response = await send_post_request(
            url="http://www.boomlings.com/database/getGJLevels21.php",
            data={'secret': _secret, "type": 5, "page": page, "str": self.player_id}
        )

        check_errors(response, LoadError, f"Something wrong had happened when fetching the user's levels.")
        if not response.split("#")[0]:
            return None
        
        return [LevelDisplay.from_raw(level_data) for level_data in response.split("#")[0].split("|")]