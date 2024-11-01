"""
# .entities.entity

A file containing all the entity classes to inherit from.
"""

from typing import List, Self, Union
from dataclasses import dataclass, field

@dataclass
class Entity:
    """
    An abstract class representing an entity. Used only for inheritance.

    Attributes
    ----------
    clients : List[Client]
        The list of clients attached to the object. Used for accounts login and interaction.
    """
    clients: List["Client"] = field(default_factory=list) # type: ignore
    """The list of clients attached to the object. Used for accounts login and interaction."""

    def add_client(self, client: "Client") -> Self: # type: ignore
        """
        Adds a client to the attached clients list.
        
        :param client: The client you want to add.
        :type client: Client
        :return: self
        """
        if not client:
            raise ValueError("client cannot be None or empty.")
        self.clients.append(client)
        return self

    def remove_client(self, client: Union["Client", int]) -> Self: # type: ignore
        """
        Remove a client to the attached clients list.
        
        :param client: The client instance or the client index you want to remove.
        :type client: Union["Client", int]
        :return: self
        """
        if isinstance(client, int):
            self.clients.pop(client)
        else:
            if client not in self.clients:
                raise ValueError("Invalid client instance, it doesn't exist in the attached clients list.")
            self.clients.remove(client)

        return self
    
    def clear_all_clients(self) -> Self:
        """
        Clear all clients from the attached clients list.
        
        :return: self
        """
        self.clients.clear()
        return self

    def add_clients(self, clients: List["Client"]) -> Self: # type: ignore
        """
        Add multiple clients to the list of clients attached.
        
        :param clients: List of clients to add.
        :type clients: List[Client]
        :return: self
        """

        if not clients:
            raise ValueError("clients cannot be None or empty.")
            
        self.clients.extend(clients)
        return self