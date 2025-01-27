from agents.rag.retrieval import FormulaRetriever
import json

formula_retriever = FormulaRetriever(collection_name="my_collection")
query_text = "Gross Profit"  # Replace with dynamic query if needed
query_results = formula_retriever.query_collection(query=query_text, n_results=2)

if query_results:
    # Process query_results as needed
    # For example, include query results in the prompt or use them in decision-making
    formatted_results = json.dumps(query_results, indent=4)
    print(f"{formatted_results}")
else:
    print ("\nNo related formulas found.")