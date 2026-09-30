const form = document.createElement('form');
form.method = 'POST';
form.action = '/cgi-bin/backupRestore.cgi';
form.enctype = 'multipart/form-data';

const postflag = document.createElement('input');
postflag.type = 'hidden';
postflag.name = 'postflag';
postflag.value = '1';
form.appendChild(postflag);

const uiStatus = document.createElement('input');
uiStatus.type = 'hidden';
uiStatus.name = 'uiStatus';
uiStatus.value = '1';
form.appendChild(uiStatus);

const fileInput = document.createElement('input');
fileInput.type = 'file';
fileInput.name = 'tools_FW_UploadFile';
form.appendChild(fileInput);

document.body.appendChild(form);
fileInput.onchange = () => form.submit();
fileInput.click();