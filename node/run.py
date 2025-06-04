import uvicorn
import ctypes

if os.name == 'nt':
    kernel32 = ctypes.windll.kernel32
    
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3006, reload=True)
