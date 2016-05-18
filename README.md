# ansible-assign-role

## About
Ansible seems to lack an ad-hoc way to assign role(s) to device(s). A simple shell script running ansible-playbook + HERE-document (i.e. https://github.com/jsmartin/ansible-tricks/ad-hoc-role/ansible-role.sh) can do the job, but if you need to pass and control more variables it might be better to write a python script using Ansible API. 
This script does exactly that. 

## How to run
```
python assign-role.py -i INVENTORY -u USERNAME -b -kK --become-user BECOME_USER ROLE(S)
```

## More info
Most of the code is just a verbatim from https://github.com/mikeputnam/misc/talks/ansible-talk/example_api_use_play.py.

Some additional useful info on the subject can be found at https://serversforhackers.com, 
[here](https://serversforhackers.com/running-ansible-programmatically)
and
[here](https://serversforhackers.com/running-ansible-2-programmatically)
