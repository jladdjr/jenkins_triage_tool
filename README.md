# jenkins_triage_tool

Annotate failures using triage notes.

## Requirements

`pip install -U -r requirements.txt`

## Sample Triage Notes

**my_triage_notes.yml**
```
---
name: My Sample Triage
tests:
  - name: test_bar
    description: still digging into this ..

  - name: test_baz
    label: failing
    description: we think the product has a genuine bug because ..

  - name: test_bam
    label: flake
    description: diagnosed flake, see issue
    links:
      - http://github.com/user/my_repo/100
```

## Sample Usage

```
cat my_list_of_failures | jenkins_triage_tool.py --notes ./my_triage_notes.yml

Not Triaged
   test_foo

Partially Triaged
   test_bar                                still digging into this ..

True Failures
   test_baz                                we think the product has a genuine bug because ..

Flakey Tests
   test_bam                                diagnosed flake, see issue
                                           - http://github.com/user/my_repo/100
```
