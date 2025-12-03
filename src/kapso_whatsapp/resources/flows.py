"""
Flows Resource

Handles WhatsApp Flows management including creation,
deployment, and preview operations.
"""

from __future__ import annotations

import builtins
import logging
from typing import TYPE_CHECKING, Any

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import WhatsAppClient

logger = logging.getLogger(__name__)


class FlowsResource(BaseResource):
    """
    WhatsApp Flows operations.

    Provides methods for:
    - Creating flows
    - Updating flow assets
    - Publishing flows
    - Getting flow previews
    - Idempotent deployment
    """

    def __init__(self, client: WhatsAppClient) -> None:
        super().__init__(client)

    async def list(
        self,
        *,
        waba_id: str,
        limit: int = 100,
        after: str | None = None,
    ) -> dict[str, Any]:
        """
        List flows for a business account.

        Args:
            waba_id: WhatsApp Business Account ID
            limit: Maximum flows to return
            after: Pagination cursor

        Returns:
            Paginated list of flows
        """
        params: dict[str, Any] = {"limit": limit}
        if after:
            params["after"] = after

        return await self._request("GET", f"{waba_id}/flows", params=params)

    async def get(self, *, flow_id: str) -> dict[str, Any]:
        """
        Get flow details.

        Args:
            flow_id: Flow ID

        Returns:
            Flow details
        """
        return await self._request("GET", flow_id)

    async def create(
        self,
        *,
        waba_id: str,
        name: str,
        categories: builtins.list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Create a new flow.

        Args:
            waba_id: WhatsApp Business Account ID
            name: Flow name
            categories: Flow categories

        Returns:
            Created flow details
        """
        payload: dict[str, Any] = {"name": name}
        if categories:
            payload["categories"] = categories

        logger.info(f"Creating flow '{name}'")
        return await self._request("POST", f"{waba_id}/flows", json=payload)

    async def update_asset(
        self,
        *,
        flow_id: str,
        asset: str | dict[str, Any],
        name: str = "flow.json",
    ) -> dict[str, Any]:
        """
        Update flow asset (JSON definition).

        Args:
            flow_id: Flow ID
            asset: Flow JSON content (string or dict)
            name: Asset name

        Returns:
            Update result
        """
        import json

        if isinstance(asset, dict):
            asset = json.dumps(asset)

        # Use multipart form data
        files = {"file": (name, asset.encode(), "application/json")}
        data = {"name": name, "asset_type": "FLOW_JSON"}

        logger.info(f"Updating flow asset for {flow_id}")
        return await self._request(
            "POST",
            f"{flow_id}/assets",
            data=data,
            files=files,
        )

    async def publish(self, *, flow_id: str) -> dict[str, Any]:
        """
        Publish a flow.

        Args:
            flow_id: Flow ID to publish

        Returns:
            Publish result
        """
        logger.info(f"Publishing flow {flow_id}")
        return await self._request("POST", f"{flow_id}/publish")

    async def deprecate(self, *, flow_id: str) -> dict[str, Any]:
        """
        Deprecate a flow.

        Args:
            flow_id: Flow ID to deprecate

        Returns:
            Deprecation result
        """
        logger.info(f"Deprecating flow {flow_id}")
        return await self._request("POST", f"{flow_id}/deprecate")

    async def delete(self, *, flow_id: str) -> dict[str, Any]:
        """
        Delete a flow.

        Args:
            flow_id: Flow ID to delete

        Returns:
            Deletion result
        """
        logger.info(f"Deleting flow {flow_id}")
        return await self._request("DELETE", flow_id)

    async def get_preview(self, *, flow_id: str) -> dict[str, Any]:
        """
        Get flow preview URL.

        Args:
            flow_id: Flow ID

        Returns:
            Preview details with URL
        """
        return await self._request(
            "GET",
            f"{flow_id}/preview",
            params={"invalidate": "true"},
        )

    async def deploy(
        self,
        flow_json: str | dict[str, Any],
        *,
        waba_id: str,
        name: str,
        publish: bool = True,
        preview: bool = False,
    ) -> dict[str, Any]:
        """
        Idempotent flow deployment.

        Creates or updates a flow, optionally publishing it.

        Args:
            flow_json: Flow JSON definition
            waba_id: WhatsApp Business Account ID
            name: Flow name
            publish: Whether to publish after upload
            preview: Whether to generate preview URL

        Returns:
            Deployment result with flow_id, published status, and optional preview_url
        """
        import json

        # Check if flow exists
        flows_response = await self.list(waba_id=waba_id, limit=100)
        existing_flow = None

        for flow in flows_response.get("data", []):
            if flow.get("name") == name:
                existing_flow = flow
                break

        # Create or get flow ID
        if existing_flow:
            flow_id = existing_flow["id"]
            logger.info(f"Found existing flow: {flow_id}")
        else:
            create_response = await self.create(waba_id=waba_id, name=name)
            flow_id = create_response["id"]
            logger.info(f"Created new flow: {flow_id}")

        # Update asset
        if isinstance(flow_json, dict):
            flow_json = json.dumps(flow_json)

        await self.update_asset(flow_id=flow_id, asset=flow_json)

        result: dict[str, Any] = {
            "flow_id": flow_id,
            "name": name,
            "published": False,
        }

        # Publish if requested
        if publish:
            try:
                await self.publish(flow_id=flow_id)
                result["published"] = True
            except Exception as e:
                logger.warning(f"Failed to publish flow: {e}")
                result["publish_error"] = str(e)

        # Get preview if requested
        if preview:
            try:
                preview_response = await self.get_preview(flow_id=flow_id)
                result["preview_url"] = preview_response.get("preview_url")
            except Exception as e:
                logger.warning(f"Failed to get preview: {e}")

        return result
