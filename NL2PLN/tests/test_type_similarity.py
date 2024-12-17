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
        
    @patch('NL2PLN.utils.ragclass.RAG')
    def test_store_and_find_types(self, mock_rag):
        """Test storing types and finding similar ones"""
        # Setup mock RAG instance
        mock_rag_instance = MagicMock()
        mock_rag.return_value = mock_rag_instance
        
        # Test storing a type
        typedef = "(: Person EntityType)"
        self.handler.store_type(typedef)
        
        mock_rag_instance.store_embedding.assert_called_with(
            {"type_name": typedef},
            ["type_name"]
        )
        
        # Test finding similar types
        mock_rag_instance.search_similar.return_value = [
            {"type_name": "Human"},
            {"type_name": "Agent"}
        ]
        
        similar_types = self.handler.find_similar_types("Person")
        self.assertEqual(len(similar_types), 2)
        self.assertEqual(similar_types[0]["type_name"], "Human")
        
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

if __name__ == '__main__':
    unittest.main()
