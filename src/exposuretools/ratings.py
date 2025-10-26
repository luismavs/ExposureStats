"""
Update photo ratings in Exposure X7 sidecar files.
"""

from pathlib import Path
from typing import Annotated
import shutil
import xml.etree.ElementTree as ET

import typer
from pydantic import BaseModel, Field, ValidationError

app = typer.Typer(help="Update photo ratings in Exposure X7 sidecar files")


class RatingValue(BaseModel):
    """Validate rating is between 0 and 5."""
    value: int = Field(ge=0, le=5)


def validate_rating(rating: int) -> int:
    """
    Validate and return a rating value between 0 and 5.
    """
    try:
        validated = RatingValue(value=rating)
        return validated.value
    except ValidationError:
        typer.secho(
            f"Error: Rating must be between 0 and 5 (got: {rating})",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)


def find_sidecar_file(photo_name: str, sidecar_dir: Path) -> Path | None:
    """
    Find the sidecar file for a given photo, trying multiple possible formats.
    
    Args:
        photo_name: The name of the photo file
        sidecar_dir: Directory containing sidecar files
        
    Returns:
        Path to the sidecar file if found, None otherwise
    """
    photo_path = Path(photo_name)
    photo_stem = photo_path.stem  # e.g., "P5300038dxo" from "P5300038dxo.jpg"
    photo_suffix = photo_path.suffix.lower()  # e.g., ".jpg" or ".jpeg"
    
    # Try different possible sidecar filename formats
    possible_names = [
        f"{photo_name}.exposurex7",  # Original filename + .exposurex7
        f"{photo_name}.exposurex6",  # Original filename + .exposurex6
        f"{photo_stem}.exposurex7",  # Stem only + .exposurex7
        f"{photo_stem}.exposurex6",  # Stem only + .exposurex6
    ]
    
    # Also try with different case variations
    for name in possible_names[:]:
        possible_names.extend([
            name.replace(".jpg", ".JPG"),
            name.replace(".jpeg", ".JPEG"),
            name.replace(".JPG", ".jpg"),
            name.replace(".JPEG", ".jpeg"),
        ])
    
    # Try to find the sidecar file
    for sidecar_name in possible_names:
        sidecar_path = sidecar_dir / sidecar_name
        if sidecar_path.exists():
            return sidecar_path
    
    return None


def update_rating_in_xml(sidecar_path: Path, rating: int) -> tuple[bool, str]:
    """
    Update the xmp:Rating attribute in the sidecar XML file.
    
    Args:
        sidecar_path: Path to the sidecar XML file
        rating: New rating value to set
        
    Returns:
        Tuple of (success: bool, old_rating: str)
    """
    try:
        # Read the original file content to preserve formatting
        with open(sidecar_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Parse XML
        tree = ET.parse(sidecar_path)
        root = tree.getroot()
        
        # Find the rdf:Description element which contains the xmp:Rating
        # This is the main element that contains all the metadata attributes
        description_elem = None
        for elem in root.iter():
            # Look for elements with rdf:about="" (the main description element)
            if elem.tag.endswith("Description") and elem.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about") == "":
                description_elem = elem
                break
        
        if description_elem is None:
            return False, "No rdf:Description element found"
        
        # Find all rating attributes and their values
        rating_attrs = []
        for attr_name, attr_value in description_elem.attrib.items():
            if attr_name.endswith("Rating") or "Rating" in attr_name:
                rating_attrs.append((attr_name, attr_value))
        
        if not rating_attrs:
            return False, "No Rating attribute found"
        
        # Map full namespace URLs to short forms used in the XML file
        namespace_mapping = {
            "{http://ns.microsoft.com/photo/1.0/}Rating": "MicrosoftPhoto:Rating",
            "{http://ns.adobe.com/xap/1.0/}Rating": "xmp:Rating",
        }
        
        # Use string replacement to preserve original formatting
        import re
        new_content = original_content
        
        # Update all rating attributes found
        for full_attr_name, old_rating in rating_attrs:
            # Get the short form of the attribute name
            short_attr_name = namespace_mapping.get(full_attr_name, full_attr_name)
            
            # Create a pattern to match the rating attribute with its value
            rating_pattern = rf'({re.escape(short_attr_name)}="){re.escape(old_rating)}(")'
            new_content = re.sub(rating_pattern, rf'\g<1>{rating}\g<2>', new_content)
            
            # If no replacement happened, try a more flexible approach
            if new_content == original_content:
                flexible_pattern = rf'({re.escape(short_attr_name)}=")[^"]*(")'
                new_content = re.sub(flexible_pattern, rf'\g<1>{rating}\g<2>', new_content)
        
        # Check if any changes were made
        if new_content == original_content:
            return False, "No changes made to content"
        
        # Write the updated content back to file
        with open(sidecar_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # Return the first rating attribute's old value for display
        return True, rating_attrs[0][1]
        
    except ET.ParseError as e:
        return False, f"XML parse error: {e}"
    except Exception as e:
        return False, f"Error updating XML: {e}"


@app.command()
def update_all_jpgs(
    source_dir: Annotated[
        Path,
        typer.Argument(
            help="Directory containing JPG files to process (where to find the filenames)",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
    root_dir: Annotated[
        Path,
        typer.Argument(
            help="Root directory containing the Exposure Software folder",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
    rating: Annotated[
        int,
        typer.Option(
            "--rating",
            "-R",
            help="Rating to assign (0-5)",
        ),
    ],
) -> None:
    """
    Update ratings for all JPG files found in the source directory.
    
    Scans the source directory recursively for JPG files and updates their ratings
    using the sidecar files located in the root directory's Exposure Software folder.
    Files without sidecar files will be skipped with a warning message.
    """
    # Validate rating using utility function
    rating = validate_rating(rating)
    
    # Find all JPG files recursively in the source directory
    jpg_files = []
    for ext in ["*.jpg", "*.jpeg", "*.JPG", "*.JPEG"]:
        jpg_files.extend(source_dir.rglob(ext))
    
    if not jpg_files:
        typer.secho(
            f"No JPG files found in {source_dir}",
            fg=typer.colors.YELLOW,
        )
        return
    
    # Convert to just filenames for the set_rating function
    photo_names = [f.name for f in jpg_files]
    
    typer.secho(
        f"Found {len(photo_names)} JPG files in {source_dir}",
        fg=typer.colors.BLUE,
    )
    typer.secho(
        f"Using Exposure Software directory: {root_dir}",
        fg=typer.colors.BLUE,
    )
    
    # Call the existing set_rating function with the root directory
    set_rating(photo_names, root_dir, rating)


@app.command()
def set_rating(
    photos: Annotated[
        list[str],
        typer.Argument(help="List of photo filenames to update"),
    ],
    root_dir: Annotated[
        Path,
        typer.Option(
            "--root-dir",
            "-r",
            help="Root directory containing the Exposure Software folder",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
    rating: Annotated[
        int,
        typer.Option(
            "--rating",
            "-R",
            help="Rating to assign (0-5)",
        ),
    ],
) -> None:
    """
    Update the xmp:Rating field in Exposure X7 sidecar files for the given photos.
    
    Creates backups of original sidecar files before modification.
    """
    # Validate rating using utility function
    rating = validate_rating(rating)
    
    # Construct paths
    sidecar_dir = root_dir / "Exposure Software" / "Exposure X7"
    backup_dir = sidecar_dir / "backup"
    
    # Verify sidecar directory exists
    if not sidecar_dir.exists():
        typer.secho(
            f"Error: Sidecar directory not found: {sidecar_dir}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)
    
    # Create backup directory if it doesn't exist
    backup_dir.mkdir(exist_ok=True)
    typer.secho(f"Backup directory: {backup_dir}", fg=typer.colors.BLUE)
    
    # Track statistics
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    # Process each photo
    for photo_name in photos:
        # Find the sidecar file using the utility function
        sidecar_path = find_sidecar_file(photo_name, sidecar_dir)
        
        if sidecar_path is None:
            typer.secho(
                f"⊘ Skipped: {photo_name} (no sidecar found)",
                fg=typer.colors.YELLOW,
            )
            skipped_count += 1
            continue
        
        # Get the sidecar filename for backup
        sidecar_name = sidecar_path.name
        
        try:
            # Create backup
            backup_path = backup_dir / sidecar_name
            shutil.copy2(sidecar_path, backup_path)
            
            # Update the rating using the utility function
            success, old_rating = update_rating_in_xml(sidecar_path, rating)
            
            if success:
                # Show old rating if it wasn't zero
                if old_rating != "0":
                    typer.secho(
                        f"✓ Updated: {photo_name} (rating: {old_rating} → {rating}) "
                        f"[previous rating was {old_rating}]",
                        fg=typer.colors.GREEN,
                    )
                else:
                    typer.secho(
                        f"✓ Updated: {photo_name} (rating: {old_rating} → {rating})",
                        fg=typer.colors.GREEN,
                    )
                updated_count += 1
            else:
                typer.secho(
                    f"⚠ Warning: {photo_name} ({old_rating})",
                    fg=typer.colors.YELLOW,
                )
                skipped_count += 1
                
        except Exception as e:
            typer.secho(
                f"✗ Error processing {photo_name}: {e}",
                fg=typer.colors.RED,
                err=True,
            )
            error_count += 1
    
    # Print summary
    typer.echo("\n" + "=" * 50)
    typer.secho("Summary:", fg=typer.colors.BLUE, bold=True)
    typer.echo(f"  Updated:  {updated_count}")
    typer.echo(f"  Skipped:  {skipped_count}")
    typer.echo(f"  Errors:   {error_count}")
    typer.echo(f"  Total:    {len(photos)}")
    typer.echo("=" * 50)


if __name__ == "__main__":
    app()