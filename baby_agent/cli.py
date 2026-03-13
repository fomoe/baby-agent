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
  baby-agent                    # Run with TUI interface (default)
  baby-agent --no-tui           # Run in interactive mode without TUI
  baby-agent -m gpt-4           # Use specific model with TUI
  baby-agent --no-tui -m gpt-4  # Interactive mode with specific model
        """
    )
    parser.add_argument(
        '-m', '--model',
        type=str,
        default="openrouter/hunter-alpha",
        help="Set the OpenAI model to use (default: openrouter/hunter-alpha)"
    )
    parser.add_argument(
        '--no-tui',
        action='store_true',
        help="Run in interactive mode without TUI interface"
    )
    args = parser.parse_args()

    # 默认使用 TUI 模式，除非指定 --no-tui
    if not args.no_tui:
        try:
            from baby_agent.tui import BabyAgentTUI
            app = BabyAgentTUI(model=args.model)
            app.run()
        except ImportError as e:
            print(f"Warning: TUI dependencies not installed. Falling back to interactive mode.")
            print(f"To use TUI, run: pip install textual rich")
            print()
            # 降级到普通模式
            try:
                agent = BabyAgent(model=args.model)
                agent.run()
            except KeyboardInterrupt:
                print("\nGoodbye!")
                sys.exit(0)
            except Exception as e:
                print(f"Error: {e}")
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
