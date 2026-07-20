# Release Process

TestPyPI betas are built manually from committed `main` without creating Git tags. Stable PyPI publication starts when an annotated `v*` tag is pushed. Docker publication remains manually dispatched against that same tag. This project does not create separate GitHub Releases.

## Prerelease

1. Use a PEP 440 prerelease version such as `2.0.14b1` in `src/bff_tools/version.py`.
2. Run the unit suite, coverage gate, documentation build, wheel smoke test, packaged annotation test, and full external CINECA chromosome 22 release gate.
3. Commit the beta release metadata and push `main`. Do not create a beta tag.
4. Configure the same OIDC trusted-publishing path used by CBIcall, without repository secrets: GitHub owner `CNAG-Biomedical-Informatics`, repository `beacon2-cbi-tools`, workflow `publish-testpypi.yml`, environment `testpypi`. TestPyPI requires this project-specific publisher entry even when the account and authorization model are shared with CBIcall.
5. Manually launch **Publish to TestPyPI** with `main` selected as the workflow ref. The workflow follows the same build, isolated-wheel test, artifact, and trusted-publishing handoff used by CBIcall.
6. Confirm the TestPyPI artifact independently without changing the system installation:

   ```bash
   python3 -m venv /tmp/bff-tools-testpypi
   version=$(python3 -c 'import runpy; print(runpy.run_path("src/bff_tools/version.py")["VERSION"])')
   /tmp/bff-tools-testpypi/bin/python -m pip install \
     --index-url https://test.pypi.org/simple/ \
     --extra-index-url https://pypi.org/simple/ \
     "beacon2-cbi-tools==$version"

   /tmp/bff-tools-testpypi/bin/bff-tools --version
   /tmp/bff-tools-testpypi/bin/bff-tools validate --check-schema
   ```

## Stable Release

1. Replace the prerelease version with the final version, update `CHANGELOG.md`, and rerun the release gates.
2. Create and push an annotated tag for the accepted commit (for example, `v2.0.13`). The tag is the release record for this project and automatically starts **Publish to PyPI**.
3. Approve the protected `pypi` environment if prompted, then verify the trusted-publishing workflow completes.
4. Manually launch the multi-architecture Docker workflow and enter the same stable tag in `release_tag`.
5. Verify that the PyPI, Git tag, and Docker versions identify the same source revision.

Never reuse a published Python version or move a stable release tag. TestPyPI and PyPI artifacts are immutable.
