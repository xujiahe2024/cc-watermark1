//env_name = process.env.CURRENT_ENV;
//console.log(process.env.CURRENT_ENV); // 输出 "TEST"

//urlprefix = "http://watermark-backend.default.svc.cluster.local";
urlprefix = "http://35.204.29.159:8071";
//switch (env_name) {
//    case "TEST": urlprefix = "http://127.0.0.1:80"; break;
//}

async function checkStatus(useAlert=true) {
    const Jobid = document.getElementById('Jobid').value;
    if(!Jobid){
        if (useAlert) alert('Please enter a job id');
        return;
    }

    try {
        const response = await fetch(urlprefix + '/status?Jobid=' + Jobid);
        if (response.ok) {
            const result = await response.json();
            const progress = result.progress;
            document.getElementById('progress').innerText = 'Progress:' + progress;
            if (progress === 100) {
                document.getElementById('Downloadbutton').setAttribute('data-jobid', Jobid);
                return 'done'
            } else {
                if (useAlert)
                    alert('Your task is still in process!')
            }
        } else {
            if (useAlert)
                alert('Fail to get status!');
        }
    } catch (error) {
        console.error('Error:', error);
        if (useAlert)
            alert('An unexpected error happened, please try again!');
    }
}


document.getElementById('Uploadform').addEventListener('submit',async function (e) {
    e.preventDefault();

    let Videofile = document.getElementById('Videofile').files[0];
    let Videourl = document.getElementById('Videourl').value;
    let Watermarkimage = document.getElementById('Watermarkimage').files[0];
    let IsFaas = document.getElementById('IsFaas').checked;

    if (!Videofile && !Videourl) {
        alert('Please upload a video or url');
        return;
    }

    if(!Watermarkimage) {
        alert('Please upload a watermark image');
        return;
    }

    const Formdata = new FormData();
    if (Videofile) Formdata.append('Videofile', Videofile);
    if (Videourl) Formdata.append('Videourl', Videourl);
    if (IsFaas) Formdata.append('IsFaas', IsFaas);
    Formdata.append('Watermarkimage',  Watermarkimage);

    try {
        const response = await fetch(urlprefix + '/upload', {
            method: 'POST',
            body: Formdata
        });

        if (response.ok) { 
            const result = await response.json();
            alert('Upload successful! Your job id is:' + result.Jobid);
            document.getElementById('displayJobid').innerText = result.Jobid;
            document.getElementById('Jobid').value = result.Jobid;

            // Start polling for status
            const statusIntervalId = setInterval(function(){
                done = checkStatus(useAlert=false);
                if (done === 'done') {
                    clearInterval(statusIntervalId);
                }
            }, 1000);  // Poll every 1 second

        } else {
            alert('Upload failed, please try again!')
        }
 
    } catch (error) {
        console.error('Error:', error);
        alert('An unexpected error happened, please try again!')
    }
});

document.getElementById('Checkstatus').addEventListener('click', function(){
    checkStatus(useAlert=true);
});

document.getElementById('Downloadbutton').addEventListener('click', function () {
    const Jobid = this.getAttribute('data-jobid');
    if (!Jobid) {
        alert('Please check your job status');
        return;
    }

    const url = urlprefix + `/download?Jobid=${Jobid}`;
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.blob();
        })
        .then(blob => {
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = downloadUrl;
            a.download = `finished_${Jobid}.mp4`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to download the video');
        });
});