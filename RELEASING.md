# Release Process

Releases are built from an explicit Git tag. All GitHub Actions workflows remain manually dispatched so that a selected tag, rather than a moving branch, determines the packaged source.

## Prerelease

1. Use a PEP 440 version such as `2.0.13b1` in `VERSION` and `src/bff_tools/version.py`; use the matching Git tag `v2.0.13b1`.
2. Run the unit suite, coverage gate, documentation build, wheel smoke test, packaged annotation test, and full external CINECA chromosome 22 release gate.
3. Commit the release metadata, create the tag, and push it.
4. Configure the same OIDC trusted-publishing path used by CBIcall, without repository secrets: GitHub owner `CNAG-Biomedical-Informatics`, repository `beacon2-cbi-tools`, workflow `publish-testpypi.yml`, environment `testpypi`. TestPyPI requires this project-specific publisher entry even when the account and authorization model are shared with CBIcall.
5. Manually launch **Publish to TestPyPI** and select the prerelease tag as the workflow ref. The workflow follows the same build, isolated-wheel test, artifact, and trusted-publishing handoff used by CBIcall.
6. Confirm the TestPyPI artifact independently without changing the system installation:

   ```bash
   python3 -m pip install \
     --index-url https://test.pypi.org/simple/ \
     --no-deps \
     --target /tmp/bff-tools-testpypi \
     "beacon2-cbi-tools==2.0.13b1"

   PYTHONPATH=/tmp/bff-tools-testpypi python3 -m bff_tools --version
   PYTHONPATH=/tmp/bff-tools-testpypi python3 -m bff_tools validate --check-schema
   ```

## Stable Release

1. Replace the prerelease version with the final version, update `Changes`, rerun the release gates, and tag the accepted commit (for example, `v2.0.13`).
2. Manually launch **Publish to PyPI** and select the stable tag. The protected `pypi` environment uses PyPI trusted publishing.
3. Create the GitHub Release from the same tag and manually launch the multi-architecture Docker workflow against it.
4. Verify that the PyPI, GitHub, and Docker versions identify the same source revision.

Never reuse a published Python version or move a release tag. TestPyPI and PyPI artifacts are immutable.
