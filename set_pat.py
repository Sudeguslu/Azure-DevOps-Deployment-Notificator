import getpass
from config import set_pat

if __name__ == "__main__":
    # getpass ekrana yazdırmadan girdi alır, terminal geçmişinde de kalmaz
    pat = getpass.getpass("Paste your Azure Devops PAT: ")
    if not pat.strip():
        print("The PAT is empty. Cancelled.")
    else:
        set_pat(pat.strip())
