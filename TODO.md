# TODO: Clean Docstrings and Comments Cleanup Plan

## Approved Plan Summary

- Remove all docstrings (""" multi-line module/function docs) and over-populated # comments (>3 lines or long explanations).
- Keep short essential # comments (e.g. # Min-heap, # OPTIONS).
- Files: All .py in algorithms/, core/, ambulance_routing/, manage.py, seed_data.py. Minor JS/CSS/HTML.
- Commit: "Fix Dp Analysis"
- Git: New branch blackboxai/clean-comments, push, gh PR.

## Steps (Completed: ~~strikethrough~~)

1. ~~[x] Create this TODO.md~~
2. [ ] Check GitHub CLI: Run `gh --version`
3. [ ] Create branch: `git checkout -b blackboxai/clean-comments`
4. [ ] Edit Python algorithm files (shortest_path.py, dp_multistop.py, etc.)
5. [ ] Edit core/ files (models.py, views.py, urls.py)
6. [ ] Edit ambulance_routing/ config files (settings.py, asgi.py, etc.)
7. [ ] Minor JS/CSS/HTML cleanups
8. [ ] `git add . && git commit -m "Fix Dp Analysis"`
9. [ ] `git push origin blackboxai/clean-comments`
10. [ ] `gh pr create --title "Fix DP Analysis: Remove docstrings/comments" --body "Removed excessive documentation as requested."`
11. [ ] Test: `python manage.py runserver`
12. [ ] Update TODO.md with completions
13. [ ] attempt_completion

**Progress: Ready for edits after Git setup.**
