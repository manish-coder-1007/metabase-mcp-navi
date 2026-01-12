"""
Image export tools for Metabase MCP.
Handles exporting cards and dashboards as images.
"""

import base64
import os
from pathlib import Path
from typing import Optional
from mcp.server.fastmcp import FastMCP

from metabase_mcp_navi.client import get_client, MetabaseClientError


def register_image_tools(mcp: FastMCP) -> None:
    """Register all image-related tools with the MCP server."""
    
    @mcp.tool()
    def get_card_image(card_id: int) -> str:
        """
        Get a card/question as a PNG image (base64 encoded).
        
        Args:
            card_id: The ID of the card to export
        
        Returns:
            Base64 encoded image data or error message
        """
        try:
            client = get_client()
            image_bytes = client.get_card_image(card_id)
            
            if not image_bytes:
                return f"❌ No image data returned for card {card_id}"
            
            # Encode to base64 for text transport
            b64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            return f"""### 🖼️ Card {card_id} Image

**Format:** PNG
**Size:** {len(image_bytes)} bytes

**Base64 Data:**
```
{b64_image[:500]}{'...' if len(b64_image) > 500 else ''}
```

*Image successfully retrieved. Use download_card_image to save to disk.*
"""
        except MetabaseClientError as e:
            if e.status_code == 400:
                return f"❌ Card {card_id} cannot be exported as image. It may be a model or have no visualization."
            elif e.status_code == 404:
                return f"❌ Card {card_id} not found"
            return f"❌ Error getting card image: {str(e)}"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def download_card_image(
        card_id: int,
        output_dir: Optional[str] = None,
        filename: Optional[str] = None
    ) -> str:
        """
        Download a card/question image and save it to disk.
        
        Args:
            card_id: The ID of the card to download
            output_dir: Directory to save the image (default: mcp-servers/output)
            filename: Optional custom filename without extension
        
        Returns:
            Success message with file path or error message
        """
        try:
            client = get_client()
            
            # Get card info for filename
            card_info = client.get(f"/api/card/{card_id}")
            card_name = card_info.get("name", f"card_{card_id}")
            
            # Get image
            image_bytes = client.get_card_image(card_id)
            
            if not image_bytes:
                return f"❌ No image data returned for card {card_id}"
            
            # Determine output path
            if output_dir:
                out_path = Path(output_dir)
            else:
                # Default to current working directory output folder
                out_path = Path.cwd() / "output"
            
            out_path.mkdir(parents=True, exist_ok=True)
            
            # Create filename
            if filename:
                safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ").strip()
            else:
                safe_name = "".join(c for c in card_name if c.isalnum() or c in "._- ").strip()
            
            if not safe_name:
                safe_name = f"card_{card_id}"
            
            file_path = out_path / f"{safe_name}.png"
            
            # Save image
            with open(file_path, 'wb') as f:
                f.write(image_bytes)
            
            return f"""### ✅ Card Image Downloaded

**Card ID:** {card_id}
**Card Name:** {card_name}
**File:** {file_path}
**Size:** {len(image_bytes)} bytes
"""
        except MetabaseClientError as e:
            if e.status_code == 400:
                return f"❌ Card {card_id} cannot be exported as image. It may be a model or have no visualization."
            elif e.status_code == 404:
                return f"❌ Card {card_id} not found"
            return f"❌ Error downloading card image: {str(e)}"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def get_dashboard_cards_as_images(dashboard_id: int) -> str:
        """
        Get all card images from a dashboard.
        Returns information about which cards can be exported as images.
        
        Args:
            dashboard_id: The ID of the dashboard
        
        Returns:
            List of cards and their image export status
        """
        try:
            client = get_client()
            
            # Get dashboard info
            dashboard = client.get(f"/api/dashboard/{dashboard_id}")
            dashboard_name = dashboard.get("name", f"Dashboard {dashboard_id}")
            
            # Get cards in dashboard
            dashcards = dashboard.get("dashcards", dashboard.get("ordered_cards", []))
            
            if not dashcards:
                return f"No cards found in dashboard {dashboard_id}"
            
            results = [f"### 📊 Dashboard: {dashboard_name}\n"]
            results.append(f"**Dashboard ID:** {dashboard_id}")
            results.append(f"**Total Cards:** {len(dashcards)}\n")
            results.append("| Card ID | Card Name | Can Export | Size |")
            results.append("| --- | --- | --- | --- |")
            
            exportable_count = 0
            
            for dc in dashcards:
                card = dc.get("card", {})
                card_id = card.get("id") if card else dc.get("card_id")
                card_name = card.get("name", "Unnamed")[:40] if card else "Unknown"
                
                if not card_id:
                    results.append(f"| - | Text/Layout | ❌ No | - |")
                    continue
                
                # Try to get image
                try:
                    image_bytes = client.get_card_image(card_id)
                    size = f"{len(image_bytes)} bytes"
                    results.append(f"| {card_id} | {card_name} | ✅ Yes | {size} |")
                    exportable_count += 1
                except:
                    results.append(f"| {card_id} | {card_name} | ❌ No | - |")
            
            results.append(f"\n**Exportable Cards:** {exportable_count}/{len(dashcards)}")
            results.append("\n*Use `download_card_image(card_id)` to save individual cards.*")
            
            return "\n".join(results)
            
        except MetabaseClientError as e:
            if e.status_code == 404:
                return f"❌ Dashboard {dashboard_id} not found"
            return f"❌ Error: {str(e)}"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"
    
    @mcp.tool()
    def download_all_dashboard_cards(
        dashboard_id: int,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Download all exportable card images from a dashboard.
        
        Args:
            dashboard_id: The ID of the dashboard
            output_dir: Directory to save images (default: output/)
        
        Returns:
            Summary of downloaded images
        """
        try:
            client = get_client()
            
            # Get dashboard info
            dashboard = client.get(f"/api/dashboard/{dashboard_id}")
            dashboard_name = dashboard.get("name", f"Dashboard {dashboard_id}")
            safe_dashboard_name = "".join(c for c in dashboard_name if c.isalnum() or c in "._- ").strip()
            
            # Determine output path
            if output_dir:
                out_path = Path(output_dir)
            else:
                out_path = Path.cwd() / "output"
            
            # Create subdirectory for dashboard
            dashboard_dir = out_path / safe_dashboard_name
            dashboard_dir.mkdir(parents=True, exist_ok=True)
            
            # Get cards
            dashcards = dashboard.get("dashcards", dashboard.get("ordered_cards", []))
            
            results = [f"### 📥 Downloading Dashboard: {dashboard_name}\n"]
            downloaded = []
            failed = []
            
            for dc in dashcards:
                card = dc.get("card", {})
                card_id = card.get("id") if card else dc.get("card_id")
                card_name = card.get("name", f"card_{card_id}") if card else f"card_{card_id}"
                
                if not card_id:
                    continue
                
                try:
                    image_bytes = client.get_card_image(card_id)
                    safe_name = "".join(c for c in card_name if c.isalnum() or c in "._- ").strip()
                    file_path = dashboard_dir / f"{safe_name}.png"
                    
                    with open(file_path, 'wb') as f:
                        f.write(image_bytes)
                    
                    downloaded.append((card_id, card_name, file_path))
                except Exception as e:
                    failed.append((card_id, card_name, str(e)))
            
            results.append(f"**Output Directory:** {dashboard_dir}\n")
            
            if downloaded:
                results.append("#### ✅ Downloaded Cards:")
                for card_id, name, path in downloaded:
                    results.append(f"- Card {card_id}: {name}")
            
            if failed:
                results.append("\n#### ❌ Failed Cards:")
                for card_id, name, error in failed:
                    results.append(f"- Card {card_id}: {name} - {error[:50]}")
            
            results.append(f"\n**Summary:** {len(downloaded)} downloaded, {len(failed)} failed")
            
            return "\n".join(results)
            
        except MetabaseClientError as e:
            return f"❌ Error: {str(e)}"
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}"
