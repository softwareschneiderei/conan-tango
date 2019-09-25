conan source . --source-folder=tmp/source
conan install . --install-folder=tmp/build
conan build . --source-folder=tmp/source --build-folder=tmp/build --package-folder=tmp/package
conan package . --build-folder=tmp/build --package-folder=tmp/package
