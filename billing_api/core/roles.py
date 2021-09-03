from typing import Optional

import httpx
from pydantic import UUID4


class RolesService:
    """Класс для работы с ролями пользователя"""

    def __init__(self, base_url):
        self.base_url = base_url
        self.roles_update_url = "api/v1/authorization/user_role/"

    async def _request(self, method: str, url: str, data: dict):
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            return await client.request(method=method, url=url, json=data)

    async def grant_role(self, user_id: UUID4, role_title: str) -> None:
        await self._request(method="POST", url=self.roles_update_url,
                            data={"user_id": str(user_id), "role_title": role_title})

    async def revoke_role(self, user_id: UUID4, role_title: str) -> None:
        await self._request(method="DELETE", url=self.roles_update_url,
                            data={"user_id": str(user_id), "role_title": role_title})


roles_client: Optional[RolesService] = None


def get_roles_client() -> Optional[RolesService]:
    return roles_client
