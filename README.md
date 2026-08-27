# HoloLink_ANPR_IRS1_v0.3.zip
HoloLink_ANPR_IRS1_v0.3.zip

Option 1 — Upload through GitHub Web
Open your repository:
HoloLink_ANPR_IRS1 on GitHub
Click Add file → Upload files.
Extract the ZIP first on your PC.
Drag the extracted project files/folders into GitHub.
Add commit message:
feat: upgrade HoloLink to v0.2 architecture
Select Create a new branch for this commit and start a pull request.
Create the branch:
feature/v0.2-architecture
Review the changes and merge after testing.
Option 2 — Recommended: Git command line

Extract the ZIP and open a terminal inside the project:

git clone https://github.com/irshadahamed007/HoloLink_ANPR_IRS1.git
cd HoloLink_ANPR_IRS1

git checkout -b feature/v0.2-architecture

Copy the new v0.2 files into this folder, then:

git add .
git status
git commit -m "feat: upgrade HoloLink to v0.2 architecture"
git push -u origin feature/v0.2-architecture

Then create a Pull Request on GitHub.

Important

Before pushing, do not upload:

.env
*.db
customer ANPR images
production credentials
API keys
passwords
private certificates

Your .env.example can be committed.

Suggested GitHub version structure
main
 │
 ├── v0.1.0
 │
 └── feature/v0.2-architecture
             │
             ├── ANPR adapters
             ├── Vehicle Intelligence
             ├── PostgreSQL
             ├── MCP
             ├── AI
             ├── Voice
             └── Monitoring

I recommend Option 2 because it keeps your current main version safe while you test HoloLink v0.2.
