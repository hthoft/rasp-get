const http = require('http');
const fs = require('fs');
const os = require('os');
const { exec } = require('child_process');

const port = 3000; // Port number for the server

const getCpuUsage = (callback) => {
    exec("top -bn1 | grep 'Cpu(s)'", (error, stdout, stderr) => {
        if (error) {
            console.error('Error getting CPU usage:', error);
            return callback(error, null);
        }
        if (stderr) {
            console.error('Error output from getting CPU usage:', stderr);
            return callback(stderr, null);
        }

        const matches = stdout.match(/(\d+\.\d+) id/);
        const idle = matches ? parseFloat(matches[1]) : null;
        const usage = idle ? 100 - idle : null;
        callback(null, usage);
    });
};

const requestHandler = (request, response) => {
    // Set CORS headers
    response.setHeader('Access-Control-Allow-Origin', '*');
    response.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    response.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, Content-Length, X-Requested-With');

    // Handle preflight OPTIONS request
    if (request.method === 'OPTIONS') {
        response.writeHead(204); // No content
        response.end();
        return;
    }

    // Handle other requests
    if (request.url === "/reboot") {
        console.log('Received request to reboot the system');

        exec('sudo reboot', (error, stdout, stderr) => {
            if (error) {
                console.error('Error trying to reboot:', error);
                response.writeHead(500);
                response.end('Server error: Unable to reboot');
                return;
            }
            response.writeHead(200);
            response.end('Reboot initiated');
        });
    } else {
        console.log('Received request for system information');

        fs.readFile('/sys/class/thermal/thermal_zone0/temp', 'utf8', (err, tempData) => {
            if (err) {
                console.error('Error reading temperature:', err);
                response.writeHead(500);
                response.end('Server error');
                return;
            }

            const temperature = tempData / 1000;

            const totalMemory = os.totalmem();
            const freeMemory = os.freemem();
            const usedMemory = totalMemory - freeMemory;
            const memoryUsage = {
                total: totalMemory,
                free: freeMemory,
                used: usedMemory
            };

            getCpuUsage((error, cpuUsage) => {
                if (error) {
                    response.writeHead(500);
                    response.end('Server error');
                    return;
                }

                response.writeHead(200, { 'Content-Type': 'application/json' });
                response.end(JSON.stringify({
                    cpuTemperature: temperature,
                    memoryUsage: memoryUsage,
                    cpuUsage: cpuUsage
                }));
            });
        });
    }
};

const server = http.createServer(requestHandler);

server.listen(port, (err) => {
    if (err) {
        console.error('Something bad happened', err);
        return;
    }

    console.log(`Server is listening on ${port}`);
});