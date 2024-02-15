# archives

Archives for TKG, but as plaintext markdown files.

## Motivation

This project came about from a "hmm, I wonder if I could do this" thought whilst reading a tech report about REST APIs for a university project.
Additionally, working on a better system for maintaining, managing and accessing the archives has been a long-term goal of the entire TKG dev team - at least for ShadowEngineer.

So when the opportunity arose to write a [ROBLOX Plugin](https://create.roblox.com/store/asset/16368745043/ArchiveParserPlugin%3Fkeyword=&pageNumber=&pagePosition=) and a Python script to move all the archives form the old storage mechanisms into this Git repository, it had to be tried...

## Using this Repository

### Archive Browsing

If you wish to just browse the archives, then by all means just go through the directories (organised into a `faction > category > entry` structure).
GitHub has a built-in markdown renderer, so viewing any of the `.md` files for the entries works in your browser!

### Editing

There are 2 primary ways of editing the archives:

1. Editing from the GitHub web app interface. (easier, but less flexible)
   - Select a file you want to edit, and click the **Edit** button on its markdown page.
   - Make your changes.
   - Once done, open a pull-request where someone with the right permissions will come and review your work, and merge if they're satisfied.
1. Editing from your local file systemm. (harder, but more flexible)
   - Follow the **Repository Setup** section (below)

## Repository Setup

Checklist of things to do (skip any that you've done before).

1. Install [Git](https://git-scm.com/)
1. Install [Python](https://www.python.org/downloads/)
1. Open a terminal, and navigate to a folder you'd like this project to go into (it'll make a new folder inside that).
1. Run `git clone https://github.com/The-Known-Galaxy/archives.git`
1. Run `cd archives` (to go into the repository folder).
1. Run `pip install toml`, `pip install mdformat-gfm`

Every time you wish to make changes:

1. Make any changes on a new branch (utilising the normal git commands (`git branch`, `git checkout`, `git status`, `git add`, `git commit`, `git pull`, `git push`) to achieve this)

## Generating the Archives

This is just a guide on how to get the latest setup of archives from the in-Studio file exports.

> **NB:** This is a ***destructive*** operation, and will most likely revert a lot of people's work if any in-repository edits have been made. This should only be done during the conversion process from Studio to GitHub (once in a lifetime, in other words).

1. Go into each of the Archive studios (if you have access), and run the [ROBLOX Plugin](https://create.roblox.com/store/asset/16368745043/ArchiveParserPlugin%3Fkeyword=&pageNumber=&pagePosition=).
1. Save the exported file into this repository, replacing any files that might already be here.
1. Run `python archive_manager.py -vgd`
