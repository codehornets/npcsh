from typing import Any, Dict, List, Optional, Union
import os
import numpy as np
try:
    from sentence_transformers import SentenceTransformer, util
except: 
    pass

def rag_search(
    query: str,
    text_data: Union[Dict[str, str], str],
    embedding_model: Any = None,
    text_data_embedded: Optional[Dict[str, np.ndarray]] = None,
    similarity_threshold: float = 0.3,
    device="cpu",
) -> List[str]:
    """
    Function Description:
        This function retrieves lines from documents that are relevant to the query.
    Args:
        query: The query string.
        text_data: A dictionary with file paths as keys and file contents as values.
        embedding_model: The sentence embedding model.
    Keyword Args:
        text_data_embedded: A dictionary with file paths as keys and embedded file contents as values.
        similarity_threshold: The similarity threshold for considering a line relevant.
    Returns:
        A list of relevant snippets.

    """
    if embedding_model is None:
        try:
            embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        except:
            raise Exception(
                "Please install the sentence-transformers library to use this function or provide an embedding transformer model."
            )
    results = []

    # Compute the embedding of the query
    query_embedding = embedding_model.encode(
        query, convert_to_tensor=True, show_progress_bar=False
    )
    if isinstance(text_data, str):
        # split at the sentence level
        lines = text_data.split(".")
        if not lines:
            return results
        # Compute embeddings for each line
        if text_data_embedded is None:
            line_embeddings = embedding_model.encode(lines, convert_to_tensor=True)
        else:
            line_embeddings = text_data_embedded
        # Compute cosine similarities
        cosine_scores = util.cos_sim(query_embedding, line_embeddings)[0].cpu().numpy()

        # Find indices of lines above the similarity threshold
        relevant_line_indices = np.where(cosine_scores >= similarity_threshold)[0]
        # print("relevant_line_indices", cosine_scores)
        # print(np.mean(cosine_scores))
        # print(np.max(cosine_scores))

        for idx in relevant_line_indices:
            idx = int(idx)
            # Get context lines (±10 lines)
            start_idx = max(0, idx - 10)
            end_idx = min(len(lines), idx + 11)  # +11 because end index is exclusive
            snippet = ". ".join(lines[start_idx:end_idx])
            results.append(snippet)

    elif isinstance(text_data, dict):
        for filename, content in text_data.items():
            # Split content into lines
            lines = content.split("\n")
            if not lines:
                continue
            # Compute embeddings for each line
            if text_data_embedded is None:
                line_embeddings = embedding_model.encode(lines, convert_to_tensor=True)
            else:
                line_embeddings = text_data_embedded[filename]
            # Compute cosine similarities
            cosine_scores = (
                util.cos_sim(query_embedding, line_embeddings)[0].cpu().numpy()
            )

            # Find indices of lines above the similarity threshold
            ##print("most similar", np.max(cosine_scores))
            ##print("most similar doc", lines[np.argmax(cosine_scores)])
            relevant_line_indices = np.where(cosine_scores >= similarity_threshold)[0]
            # print("relevant_line_indices", cosine_scores)
            # print(np.mean(cosine_scores))
            # print(np.max(cosine_scores))
            for idx in relevant_line_indices:
                idx = int(idx)  # Ensure idx is an integer
                # Get context lines (±10 lines)
                start_idx = max(0, idx - 10)
                end_idx = min(
                    len(lines), idx + 11
                )  # +11 because end index is exclusive
                snippet = "\n".join(lines[start_idx:end_idx])
                results.append((filename, snippet))
        # print("results", results)
    return results




def load_all_files(
    directory: str, extensions: List[str] = None, depth: int = 1
) -> Dict[str, str]:
    """
    Function Description:
        This function loads all text files in a directory and its subdirectories.
    Args:
        directory: The directory to search.
    Keyword Args:
        extensions: A list of file extensions to include.
        depth: The depth of subdirectories to search.
    Returns:
        A dictionary with file paths as keys and file contents as values.
    """
    text_data = {}
    if depth < 1:
        return text_data  # Reached the specified depth, stop recursion.

    if extensions is None:
        # Default to common text file extensions
        extensions = [
            ".txt",
            ".md",
            ".py",
            ".java",
            ".c",
            ".cpp",
            ".html",
            ".css",
            ".js",
            ".ts",
            ".tsx",
            ".npc",
            # Add more extensions if needed
        ]

    try:
        # List all entries in the directory
        entries = os.listdir(directory)
    except Exception as e:
        print(f"Could not list directory {directory}: {e}")
        return text_data

    for entry in entries:
        path = os.path.join(directory, entry)
        if os.path.isfile(path):
            if any(path.endswith(ext) for ext in extensions):
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as file:
                        text_data[path] = file.read()
                except Exception as e:
                    print(f"Could not read file {path}: {e}")
        elif os.path.isdir(path):
            # Recurse into subdirectories, decreasing depth by 1
            subdir_data = load_all_files(path, extensions, depth=depth - 1)
            text_data.update(subdir_data)

    return text_data
