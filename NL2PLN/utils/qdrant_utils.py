import json
import argparse
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

def main():
    parser = argparse.ArgumentParser(description='Qdrant collection backup and restore utility')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Dump command
    dump_parser = subparsers.add_parser('dump', help='Dump collection to file')
    dump_parser.add_argument('collection', help='Collection name')
    dump_parser.add_argument('output', help='Output file path')
    dump_parser.add_argument('--limit', type=int, help='Maximum number of points to retrieve')
    dump_parser.add_argument('--url', default='localhost:6334', help='Qdrant server URL')

    # Populate command
    populate_parser = subparsers.add_parser('populate', help='Populate collection from file')
    populate_parser.add_argument('collection', help='Collection name')
    populate_parser.add_argument('input', help='Input file path')
    populate_parser.add_argument('--url', default='localhost:6334', help='Qdrant server URL')
    populate_parser.add_argument('--batch-size', type=int, default=100, help='Batch size for inserts')

    args = parser.parse_args()

    if args.command == 'dump':
        dump_collection(
            collection_name=args.collection,
            output_file=args.output,
            limit=args.limit,
            qdrant_url=args.url
        )
        print(f"Collection '{args.collection}' dumped to {args.output}")
    
    elif args.command == 'populate':
        populate_collection(
            collection_name=args.collection,
            input_file=args.input,
            qdrant_url=args.url,
            batch_size=args.batch_size
        )
        print(f"Collection '{args.collection}' populated from {args.input}")

if __name__ == '__main__':
    main()
