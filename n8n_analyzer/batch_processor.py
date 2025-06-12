# n8n_analyzer/batch_processor.py
import argparse
import logging
import os
import time
from typing import Optional, Callable, List, Any, Dict # Added Dict here

from n8n_analyzer.core.parser import stream_workflows_from_directory, N8nWorkflow

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)

class WorkflowBatchProcessor:
    """
    A framework for batch processing n8n workflow files from a directory.
    """
    def __init__(self, workflow_dir: str):
        if not os.path.isdir(workflow_dir):
            msg = f"Workflow directory not found or is not a directory: {workflow_dir}"
            logger.error(msg)
            raise ValueError(msg)
        self.workflow_dir = workflow_dir
        self.total_files_scanned = 0
        self.successfully_parsed_workflows = 0
        self.failed_to_parse_count = 0

    def process_workflows(self,
                          workflow_handler: Optional[Callable[[N8nWorkflow], None]] = None,
                          limit: Optional[int] = None) -> List[Any]:
        """
        Processes workflows from the directory using the stream_workflows_from_directory parser.

        Args:
            workflow_handler: An optional callable that takes an N8nWorkflow object
                              and performs some action (e.g., analysis, storage).
            limit: Optional maximum number of workflows to process.

        Returns:
            A list of results from the workflow_handler, if provided.
        """
        logger.info(f"Starting batch processing of workflows from directory: {self.workflow_dir}")
        start_time = time.time()

        results = []
        processed_count = 0

        for workflow in stream_workflows_from_directory(self.workflow_dir):
            self.total_files_scanned += 1
            if workflow:
                self.successfully_parsed_workflows += 1
                logger.debug(f"Successfully parsed: {workflow.name} (Path: {workflow.file_path})")
                if workflow_handler:
                    try:
                        result = workflow_handler(workflow)
                        if result is not None:
                            results.append(result)
                    except Exception as e:
                        logger.error(f"Error processing workflow {workflow.name} with handler: {e}")
                else:
                    logger.info(f"Processed workflow: {workflow.name} - Nodes: {len(workflow.nodes)}, Connections: {len(workflow.connections)}")
            else:
                self.failed_to_parse_count +=1
                logger.warning("Encountered a workflow that could not be parsed (parser returned None).")

            processed_count += 1
            if limit is not None and processed_count >= limit:
                logger.info(f"Reached processing limit of {limit} workflows.")
                break

        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Batch processing completed in {duration:.2f} seconds.")
        logger.info(f"Successfully parsed workflows: {self.successfully_parsed_workflows}")

        if self.failed_to_parse_count > 0:
             logger.warning(f"Number of files that failed to parse into workflow objects: {self.failed_to_parse_count}")


        return results

def simple_workflow_analyzer(workflow: N8nWorkflow) -> Optional[Dict[str, Any]]:
    """A simple example of a workflow handler."""
    if workflow is None:
        return None
    analysis_summary = {
        "name": workflow.name,
        "node_count": len(workflow.nodes),
        "connection_count": len(workflow.connections),
        "is_active": workflow.active,
        "first_node_type": workflow.nodes[0].type if workflow.nodes else None
    }
    logger.info(f"Analyzing: {workflow.name} - Nodes: {analysis_summary['node_count']}")
    return analysis_summary


def main():
    """Main function to run the batch processor from the command line."""
    parser = argparse.ArgumentParser(description="Batch process n8n workflow JSON files.")
    parser.add_argument("workflow_dir",
                        type=str,
                        help="Directory containing n8n workflow .json files.")
    parser.add_argument("--limit",
                        type=int,
                        default=None,
                        help="Maximum number of workflows to process.")
    parser.add_argument("--analyze",
                        action="store_true",
                        help="Run a simple analysis on each workflow.")

    args = parser.parse_args()

    try:
        processor = WorkflowBatchProcessor(args.workflow_dir)
        handler = None
        if args.analyze:
            logger.info("Simple analysis enabled.")
            handler = simple_workflow_analyzer
        results = processor.process_workflows(workflow_handler=handler, limit=args.limit)
        if args.analyze and results:
            logger.info(f"Analysis results for {len(results)} workflows collected.")
    except ValueError as e:
        logger.error(f"Initialization error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during batch processing: {e}", exc_info=True)

if __name__ == "__main__":
    main()
