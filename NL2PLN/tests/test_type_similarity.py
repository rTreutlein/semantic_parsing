import unittest
from unittest.mock import patch, MagicMock
from NL2PLN.utils.type_similarity import TypeSimilarityHandler

class TestTypeSimilarityHandler(unittest.TestCase):
    def setUp(self):
        self.handler = TypeSimilarityHandler(collection_name="test_types")
        
    def test_extract_type_name(self):
        """Test type name extraction from typedef statements"""
        test_cases = [
            ("(: Person EntityType)", "Person"),
            ("(: Animal LivingThing)", "Animal"),
            ("invalid typedef", None),
            ("(: )", None),
            ("", None)
        ]
        
        for typedef, expected in test_cases:
            with self.subTest(typedef=typedef):
                result = self.handler.extract_type_name(typedef)
                self.assertEqual(result, expected)
                
    @patch('NL2PLN.utils.type_similarity.create_openai_completion')
    def test_analyze_type_similarities(self, mock_completion):
        """Test similarity analysis between types"""
        mock_completion.return_value = "(Inheritance Person Human)\n(Similarity Person Agent)"
        
        new_type = "Person"
        similar_types = [
            {"type_name": "Human"},
            {"type_name": "Agent"}
        ]
        
        expected = ["(Inheritance Person Human)", "(Similarity Person Agent)"]
        result = self.handler.analyze_type_similarities(new_type, similar_types)
        
        self.assertEqual(result, expected)
        mock_completion.assert_called_once()
        
    def test_process_new_typedefs(self):
        """Test processing multiple type definitions"""
        with patch.object(self.handler, 'find_similar_types') as mock_find, \
             patch.object(self.handler, 'analyze_type_similarities') as mock_analyze, \
             patch.object(self.handler, 'store_type') as mock_store:
            
            # Setup mocks
            mock_find.return_value = [{"type_name": "Human"}]
            mock_analyze.return_value = ["(Inheritance Person Human)"]
            
            typedefs = [
                "(: Person EntityType)",
                "(: Animal LivingThing)",
                "invalid typedef"
            ]
            
            linking_statements = self.handler.process_new_typedefs(typedefs)
            
            # Verify results
            self.assertEqual(len(linking_statements), 2)  # One for each valid typedef
            self.assertEqual(mock_store.call_count, 3)  # Called for all typedefs
            self.assertEqual(mock_analyze.call_count, 2)  # Called for valid typedefs only

    def test_action_type_relationships(self):
        """Test handling of related action types like LeaveSomething and Take"""
        with patch.object(self.handler, 'find_similar_types') as mock_find, \
             patch.object(self.handler, 'analyze_type_similarities') as mock_analyze:

            # Setup mocks
            mock_find.return_value = [{"type_name": "(: Take (-> Object Object Type))"}]
            mock_analyze.return_value = ["(: LeaveSomethingToTake (-> (: $l (LeaveSomething $a $b)) (Not (Take $a $b))))"]

            new_type = "(: LeaveSomething (-> Object Object Type))"
            similar_types = self.handler.find_similar_types(new_type)
            linking_statements = self.handler.analyze_type_similarities(new_type, similar_types)

            # Verify the relationship was correctly identified
            self.assertEqual(len(linking_statements), 1)
            self.assertIn("LeaveSomethingToTake", linking_statements[0])
            self.assertIn("Not", linking_statements[0])

def main():
    """Interactive loop for testing type similarities"""
    handler = TypeSimilarityHandler("testingloop")
    print("Type Similarity Interactive Tester")
    print("Enter type definitions one per line. Empty line to analyze, 'quit' to exit.")
    
    while True:
        typedefs = []
        while True:
            line = input("> ").strip()
            if line.lower() == 'quit':
                return
            if not line:
                break
            typedefs.append(line)
            
        if typedefs:
            print("\nAnalyzing types...")
            linking_statements = handler.process_new_typedefs(typedefs)
            if linking_statements:
                print("\nFound relationships:")
                for stmt in linking_statements:
                    print(stmt)
            else:
                print("\nNo clear relationships found.")
            print("\nEnter more types or 'quit' to exit.")

if __name__ == '__main__':
    main()
