# Developer Certificate of Origin (DCO)

## Overview

`pacsanini` enforces the Developer Certificate of Origin on PRs.

The Developer Certificate of Origin (DCO) is a lightweight way for contributors to certify that they wrote or otherwise have the right to submit the code they are contributing to the project. Here is the full [text of the DCO](https://developercertificate.org/), reformatted for readability:

> By making a contribution to this project, I certify that:
>
> (a) The contribution was created in whole or in part by me and I have the right to submit it under the open source license indicated in the file; or
>
> (b) The contribution is based upon previous work that, to the best of my knowledge, is covered under an appropriate open source license and I have the right under that license to submit that work with modifications, whether created in whole or in part by me, under the same open source license (unless I am permitted to submit under a different license), as indicated in the file; or
>
> (c) The contribution was provided directly to me by some other person who certified (a), (b) or (c) and I have not modified it.
>
> (d) I understand and agree that this project and the contribution are public and that a record of the contribution (including all personal information I submit with it, including my sign-off) is maintained indefinitely and may be redistributed consistent with this project or the open source license(s) involved.

## How to sign-off commits

Each commit you submit as part of a PR must be signed off in the following way:

```
Signed-off-by: jdoe <john.doe@example.com>
```

You can use your GitHub alias but the email address must be yours and active.

You can either write the above snippet in your commit message or you can use the `-s/--signoff` command line option when running `git commit`. For example:

```bash
git commit -s -m "My commit message"
```

For this to be effective, ensure that your git credentials are correctly set.

Your username can be set with:

```bash
git config user.name "jdoe"
```

Your email can be set with:

```bash
git config user.email "john.doe@example.com"
```

## Amending unsigned commits

If you did not signoff one or multiple commits on your branch, you can always amend these commits with the following command on your feature branch:

```bash
git commit --amend --signoff
```

If you have already pushed your commits to a remote, you can still push the signed commits using:

```bash
git push --force-with-lease
```
