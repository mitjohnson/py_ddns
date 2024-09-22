const email = "";
let apiKey = ""
const authMethod = "token";                                    // token or global
const zoneID = "";                                             // found in overview tab
const dnsTTL = 3600;
const recordName = "";                                         // example.com
const proxy = true;
const cloudFlareURL = `https://api.cloudflare.com/client/v4/zones/${zoneID}/dns_records?type=A&name=${recordName}`;

const getIP = async () => {
    const websites = ["https://api.ipify.org","https://cloudflare.com/cdn-cgi/trace"];

    try{
        const response = await fetch(websites[0]);
        if (!response.ok){
            console.warn(`Ipify failed - Response status: ${response.status}`);
            response = await fetch(websites[1]);
            if (!response.ok){
                throw new Error(`Response status: ${response.status}`);
            };
        };

        const data = await response.text();
        const ip = data;

        if (websites === websites[1]){
            data = data.split('\n');
            ip = data[2].slice(3);
        };
        return ip;
    } catch(error){
        console.error(error.message);
    };
};

const getAuthHeaders = () => {
    // craft auth headers
    let authHeader = "";

    if (authMethod.toLowerCase() === "global"){
        authHeader = "X-Auth-Key";
        return authHeader;
    } else{
        authHeader = "Authorization"; 
        let newApiKey = "Bearer " + apiKey;
        return [authHeader, newApiKey];
    };
};

const getCloudInfo = async (cloudFlareURL) => {  
    // Query cloudflare for old IP and Record ID.
    const authHeader = getAuthHeaders();

    try{
        const cloudflare = await fetch(cloudFlareURL,{
            headers: {
                "X-Auth-Email": email,
                [authHeader[0]]: authHeader[1],
                "Content-Type": "application/json",
            }, 
        });
        
        if (!cloudflare.ok){
            throw new Error(`Response status: ${cloudflare.status}`)
        };

        const reply = await cloudflare.json();
        console.log(reply);
        const oldIP = await reply["result"][0]["content"];
        const recordID = await reply["result"][0]["id"];
        return [oldIP, recordID];

    } catch (error){
        console.error(error.message);
    };
};

const updateCF = async () => {  
    // get old IP & record ID
    const cloudInfo = await getCloudInfo(cloudFlareURL);
    console.log(cloudInfo);
    const oldIP = await cloudInfo[0];
    const recordID = await cloudInfo[1];

    // get current IP
    const currIP = await getIP();
    
    // compare IP adresses
    if (oldIP !== currIP){
        // get headers
        const authHeaders = getAuthHeaders();
        // patch new IP adress to cloudflare
        try{
            const patch = await fetch(`https://api.cloudflare.com/client/v4/zones/${zoneID}/dns_records/${recordID}`, {
                method: "PATCH",
                headers: {
                    "X-Auth-Email": email,
                    [authHeaders[0]]: authHeaders[1],
                    "Content-Type": "application/json",
                }, 
                body: JSON.stringify({
                    "content": currIP,
                    "name": recordName,
                    "type": "A",
                    "proxied": proxy,
                    "ttl": dnsTTL 
                }),
            });

            const reply = await patch.json();
            console.log(reply.errors);
            if (!patch.ok){
                throw new Error(`Response status: ${patch.status}, ${reply.errors}`)
            }
            console.log(`IP changed from ${oldIP} to ${currIP} on ${recordName}`);
        } catch (error) {
            console.log(error.message);
        };
    } else {
        console.log(`IP: ${currIP} is up to date and has not changed.`)
    };
};
updateCF();

