import sys
import argparse
from baby_agent.agent import BabyAgent

def main():
    """Main entry point for the baby-agent command"""
    parser = argparse.ArgumentParser(
        description="Baby Agent - A smart command-line agent with OpenAI integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  baby-agent                    # Run in interactive mode
  baby-agent --tui              # Run with TUI interface
  baby-agent -m gpt-4           # Use specific model
  baby-agent --tui -m gpt-4     # TUI mode with specific model
        """
    )
    parser.add_argument(
        '-m', '--model',
        type=str,
        default="openrouter/hunter-alpha",
        help="Set the OpenAI model to use (default: openrouter/hunter-alpha)"
    )
    parser.add_argument(
        '--tui',
        action='store_true',
        help="Run with Textual TUI interface"
    )
    args = parser.parse_args()

    # 如果指定了 TUI 模式，启动 TUI
    if args.tui:
        try:
            from baby_agent.tui import BabyAgentTUI
            app = BabyAgentTUI(model=args.model)
            app.run()
        except ImportError as e:
            print(f"Error: TUI dependencies not installed. Run: pip install textual rich")
            print(f"Details: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"TUI Error: {e}")
            sys.exit(1)
    else:
        # 普通交互模式
        try:
            agent = BabyAgent(model=args.model)
            agent.run()
        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
