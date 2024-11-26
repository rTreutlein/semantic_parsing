import json
from typing import Optional, List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

def dump_collection(
    collection_name: str,
    output_file: str,
    limit: Optional[int] = None,
    qdrant_url: str = "localhost:6334"
) -> None:
    """
    Dumps all or n elements from a Qdrant collection to a file.
    
    Args:
        collection_name: Name of the Qdrant collection
        output_file: Path to output file
        limit: Maximum number of points to retrieve (None for all)
        qdrant_url: URL of the Qdrant server
    """
    client = QdrantClient(qdrant_url)
    
    # Scroll through all points in collection
    points = []
    offset = None
    batch_size = 100
    
    while True:
        batch = client.scroll(
            collection_name=collection_name,
            limit=batch_size,
            offset=offset
        )[0]
        
        if not batch:
            break
            
        points.extend([
            {
                "id": point.id,
                "payload": point.payload,
                "vector": point.vector.tolist() if point.vector is not None else None
            }
            for point in batch
        ])
        
        if limit and len(points) >= limit:
            points = points[:limit]
            break
            
        offset = batch[-1].id

    # Write to file
    with open(output_file, 'w') as f:
        json.dump(points, f, indent=2)

def populate_collection(
    collection_name: str,
    input_file: str,
    qdrant_url: str = "localhost:6334",
    batch_size: int = 100
) -> None:
    """
    Populates a Qdrant collection from a file created by dump_collection.
    
    Args:
        collection_name: Name of the Qdrant collection
        input_file: Path to input file containing collection data
        qdrant_url: URL of the Qdrant server
        batch_size: Number of points to upsert in each batch
    """
    client = QdrantClient(qdrant_url)
    
    # Read points from file
    with open(input_file, 'r') as f:
        points = json.load(f)
    
    # Insert points in batches
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        
        point_structs = [
            PointStruct(
                id=p["id"],
                payload=p["payload"],
                vector=p["vector"]
            )
            for p in batch
        ]
        
        client.upsert(
            collection_name=collection_name,
            points=point_structs
        )
