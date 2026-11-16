import asyncio
import sys

async def test():
    with open("test_stderr.log", "w") as f:
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                "-c",
                "import sys; sys.stderr.write('hello stderr\\n'); sys.stdout.write('hello stdout\\n')",
                stdout=f,
                stderr=asyncio.subprocess.STDOUT,
            )
            await proc.wait()
            print("SUCCESS")
        except Exception as e:
            print("EXCEPTION:", type(e), e)

if __name__ == "__main__":
    asyncio.run(test())
    print("LOG CONTENT:", open("test_stderr.log").read())
