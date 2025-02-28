---
name: Release Cleanup
about: Minor tasks and checklist for maintainer to cleanup and prepare a release
title: 'Cleanup and prepare RELEASE_VERSION'
labels: documentation, internal
assignees: 'mikkonie'

---

## Minor Tasks

TBA

## Issues to Add in CHANGELOG

TBA

## Release Checklist

- [ ] Review code style and cleanup if needed
- [ ] Review and update doc entries if needed
- [ ] Ensure all relevant updates are in `CHANGELOG` and major changes doc
- [ ] Ensure REST API versions are up to date and documented
- [ ] Upgrade version number of pypi package reference in `README`
- [ ] Upgrade docs config version number (usually at `x.y.z-WIP` when developing)
- [ ] Update latest version info in `codemeta.json`
- [ ] Update version number and date in `CHANGELOG`
- [ ] Update version number and date in `Major Changes` doc
- [ ] Ensure docs can be built without errors
- [ ] Ensure `make spectacular` runs without errors or warnings (until in CI)

## Notes

N/A
