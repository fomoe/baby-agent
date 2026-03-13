import sys
import argparse
from baby_agent.agent import BabyAgent

def main():
    """Main entry point for the baby-agent command"""
    parser = argparse.ArgumentParser(description="Baby Agent - A smart command-line agent with OpenAI integration")
    parser.add_argument('-m', '--model', type=str, default="openrouter/hunter-alpha", help="Set the OpenAI model to use")
    args = parser.parse_args()
    
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
