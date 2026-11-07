# org-github — staged contents of the `.github` repository

These are the organisation-level community files (IMP-M21-08, D11): once `turnbase-platform/.github` exists
they are copied to its root and this directory is deleted. They live here only because creating a
repository is an owner decision.

```bash
gh repo create turnbase-platform/.github --private --description "TurnBase organisation profile and community health files"
git clone git@github.com:turnbase-platform/.github.git /tmp/dotgithub
cp -r org-github/{CONTRIBUTING.md,SECURITY.md,CODE_OF_CONDUCT.md,profile} /tmp/dotgithub/
# commit and push from /tmp/dotgithub (its own default branch), then:
scripts/repo-settings.sh --apply .github
```
