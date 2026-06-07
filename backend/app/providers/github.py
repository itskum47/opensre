import httpx
import logging
from typing import Dict, Any, List
from sdk.plugin import DataSourcePlugin
from backend.app.config.settings import settings

logger = logging.getLogger(__name__)

class GitHubDataSource(DataSourcePlugin):
    def __init__(self, token: str = None, repo: str = None, mock: bool = False):
        self.token = token or settings.GITHUB_TOKEN
        self.repo = repo or settings.GITHUB_REPO
        self.mock = mock or (settings.API_ENV == "development")

    def get_source_type(self) -> str:
        return "github"

    async def collect_evidence(self, investigation_id: str, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        since = query_params.get("since")
        until = query_params.get("until")
        repo = query_params.get("repo", self.repo)
        
        is_mock = query_params.get("mock", self.mock)
        
        if is_mock or not repo:
            # Return realistic mock GitHub commits
            mock_payload = [
                {
                    "sha": "a1b2c3d4e5f6g7h8i9j0",
                    "commit": {
                        "message": "fix(auth): handle null token exception in validation filter",
                        "author": {
                            "name": "Kumar Mangalam",
                            "email": "kumarmangalam314@outlook.com",
                            "date": since or "2026-06-07T10:00:00Z"
                        }
                    },
                    "html_url": f"https://github.com/{repo or 'owner/repo'}/commit/a1b2c3d4e5f6g7h8i9j0"
                },
                {
                    "sha": "f9e8d7c6b5a432109876",
                    "commit": {
                        "message": "feat(gateway): rate limit incoming requests",
                        "author": {
                            "name": "Kumar Mangalam",
                            "email": "kumarmangalam314@outlook.com",
                            "date": since or "2026-06-07T09:30:00Z"
                        }
                    },
                    "html_url": f"https://github.com/{repo or 'owner/repo'}/commit/f9e8d7c6b5a432109876"
                }
            ]
            return [{
                "source_id": "repository_commits",
                "payload": mock_payload
            }]

        url = f"https://api.github.com/repos/{repo}/commits"
        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.token and self.token != "mock-token":
            headers["Authorization"] = f"Bearer {self.token}"
            
        params = {}
        if since:
            params["since"] = since
        if until:
            params["until"] = until
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params, timeout=10.0)
                response.raise_for_status()
                return [{
                    "source_id": "repository_commits",
                    "payload": response.json()
                }]
        except Exception as e:
            logger.error(f"Failed to fetch GitHub commits for {repo}: {e}")
            raise e
