import argparse
import sys
import sqlite3
from langgraph.checkpoint.memory import MemorySaver  # type: ignore
from langgraph.types import Command  # type: ignore
import config.settings as settings
from src.database import init_db
from src.graph import build_graph

def main():
    parser = argparse.ArgumentParser(description="Queue Maintenance AI Agent CLI")
    parser.add_argument("--query", type=str, help="Instruction for the agent")
    parser.add_argument("--resume", type=str, help="Resume an interrupted action with Y or N")
    parser.add_argument("--thread_id", type=str, default="cli_thread_1", help="Thread ID for graph memory")
    parser.add_argument("--inspect", action="store_true", help="Inspect current queue")
    args = parser.parse_args()

    # Initialize DB safely on startup
    init_db()

    if args.inspect:
        conn = sqlite3.connect(settings.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM content_queue")
        rows = cursor.fetchall()
        print(f"Current Queue ({len(rows)} items):")
        for r in rows:
            print(dict(r))
        conn.close()
        return

    memory_saver = MemorySaver()
    app = build_graph().compile(checkpointer=memory_saver)
    config = {"configurable": {"thread_id": args.thread_id}}

    if args.resume:
        app.invoke(Command(resume=args.resume), config)
        state = app.get_state(config).values
        print("Final Result:", state.get("final_result"))
        return

    if args.query:
        initial_state = {"messages": [{"role": "user", "content": args.query}]}
        app.invoke(initial_state, config)
        
        state = app.get_state(config)
        if len(state.next) > 0 and state.next[0] == "human_review_node":
            pending_actions = state.values.get("proposed_actions", [])
            print(f"Agent wants to execute: {pending_actions}")
            print("To approve or reject, run with: --resume Y  or --resume N")
        else:
            print("Final Result:", state.values.get("final_result"))
        return

    parser.print_help()

if __name__ == "__main__":
    main()
