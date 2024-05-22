import secrets
import string

from wialon import flags as wialon_flag
from .session import WialonSession, WialonBase

from typing import Union, Optional


class WialonUser(WialonBase):
    class WialonPassword:
        def __init__(self, length: int) -> None:
            self._length = length
            self._password = self.gen_password(length)

        @property
        def raw(self) -> str:
            return self._password

        def gen_password(self, length: int = 8) -> str:
            """
            Create a random Wialon API compliant password.

            Parameters
            ----------
            length: <int>
                The length of the password.

            Returns
            -------
            password: <str>
                The password.

            Password Requirements
            ---------------------
            - At least one lowercase letter
            - At least one number
            - At least one special character
            - At least one uppercase letter
            - Different from username
            - Minumum 8 charcters

            """
            length += 1
            letters: tuple = tuple(string.ascii_letters)
            numbers: tuple = tuple(string.digits)
            symbols: tuple = ("@", "#", "$", "%")

            while True:
                password = "".join(
                    secrets.choice(letters + numbers + symbols) for i in range(length)
                )
                if (
                    any(c.islower() for c in password)
                    and any(c.isupper() for c in password)
                    and sum(c.isdigit() for c in password) >= 3
                ):
                    break

            return password

        # TODO
        def refresh_password(self) -> None:
            raise NotImplementedError
            with WialonSession() as session:
                session.wialon_api.core_reset_password(**{})

    def __init__(
        self, email: Optional[str] = None, id: Union[int, None] = None
    ) -> None:
        if (id is not None and email is not None) or (id is None and email is None):
            raise ValueError("Either email or id must be provided, but not both.")

        if email:
            self.init_by_email(email)
        elif id:
            self.init_by_id(id)

        return None

    def init_by_id(self, id: int) -> None:
        with WialonSession() as session:
            self._id = id
            self._name = self.get_name(id, session)
            self._password = self.WialonPassword(8).raw

        return None

    def init_by_email(self, email: str) -> None:
        with WialonSession() as session:
            self._name = email
            self._password = self.WialonPassword(8).raw
            self._id = self.create(session)
            self.set_new_userflags(session)

        return None

    @property
    def name(self) -> str:
        return self._name

    @property
    def email(self) -> str:
        return self._name

    @property
    def password(self) -> str:
        return self._password

    def get_name(self, id: int, session: WialonSession) -> str:
        params = {
            "id": id,
            "flags": wialon_flag.ITEM_DATAFLAG_BASE,
        }
        response = session.wialon_api.core_search_item(**params)
        name = response.get("item").get("nm")
        return name

    def set_new_userflags(self, session: WialonSession) -> None:
        params = {
            "itemId": self.id,
            "flags": (
                wialon_flag.ITEM_USER_USERFLAG_CANNOT_CHANGE_SETTINGS
                + wialon_flag.ITEM_USER_USERFLAG_CANNOT_CHANGE_PASSWORD
            ),
            "flagsMask": (
                wialon_flag.ITEM_USER_USERFLAG_CANNOT_CHANGE_SETTINGS
                - wialon_flag.ITEM_USER_USERFLAG_CANNOT_CHANGE_PASSWORD
            ),
        }
        session.wialon_api.core_update_user(**params)

        return None

    def create(self, session: WialonSession) -> int:
        params = {
            "creatorId": 27881459,  # Terminus 1000's Wialon ID
            "name": self.name,
            "password": self.password,
            "dataFlags": wialon_flag.ITEM_DATAFLAG_BASE,
        }
        response = session.wialon_api.core_create_user(**params)
        id = response.get("item").get("id")
        return id