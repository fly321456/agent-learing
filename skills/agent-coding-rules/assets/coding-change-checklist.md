# Coding Change Checklist

## Before Coding

- Which layer is changing?
- What responsibility should stay out of this layer?
- What is the smallest complete improvement?

## During Coding

- Are prompt, tool, session, and runtime concerns still separated?
- Did the change make the interface clearer for the model?
- Did the change reduce or increase ambiguity?

## Before Finishing

- What evidence shows this works?
- What failure path was considered?
- What future debugging signal now exists?
- Should a learning note also be updated?
