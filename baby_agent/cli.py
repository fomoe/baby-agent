import sys
from baby_agent.agent import BabyAgent

def main():
    """Main entry point for the baby-agent command"""
    try:
        agent = BabyAgent()
        agent.run()
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
