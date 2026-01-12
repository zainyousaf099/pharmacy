const dgram = require('dgram');
const EventEmitter = require('events');

class NetworkDiscovery extends EventEmitter {
    constructor() {
        super();
        this.BROADCAST_PORT = 8765;
        this.DISCOVER_INTERVAL = 3000;
        this.serverIP = null;
        this.isServer = false;
        this.discoverySocket = null;
        this.broadcastSocket = null;
    }

    // Start discovery process
    startDiscovery() {
        console.log('Starting network discovery...');
        
        // Listen for server broadcasts
        this.discoverySocket = dgram.createSocket('udp4');
        
        this.discoverySocket.on('message', (msg, rinfo) => {
            try {
                const data = JSON.parse(msg.toString());
                if (data.type === 'clinic-server' && !this.isServer) {
                    console.log(`Found server at ${rinfo.address}`);
                    this.serverIP = rinfo.address;
                    this.emit('server-found', rinfo.address);
                    this.stopDiscovery();
                }
            } catch (err) {
                // Ignore invalid messages
            }
        });

        this.discoverySocket.on('error', (err) => {
            console.error('Discovery socket error:', err);
        });

        this.discoverySocket.bind(this.BROADCAST_PORT, () => {
            console.log(`Listening for servers on port ${this.BROADCAST_PORT}`);
        });

        // Wait 5 seconds for server response
        setTimeout(() => {
            if (!this.serverIP) {
                console.log('No server found - becoming server');
                this.becomeServer();
            }
        }, 5000);
    }

    // Become the server and broadcast presence
    becomeServer() {
        this.isServer = true;
        this.emit('become-server');
        
        this.broadcastSocket = dgram.createSocket('udp4');
        this.broadcastSocket.bind(() => {
            this.broadcastSocket.setBroadcast(true);
            console.log('Broadcasting as server...');
        });

        // Broadcast server presence every 3 seconds
        this.broadcastInterval = setInterval(() => {
            const message = JSON.stringify({
                type: 'clinic-server',
                timestamp: Date.now()
            });

            this.broadcastSocket.send(
                message,
                0,
                message.length,
                this.BROADCAST_PORT,
                '255.255.255.255',
                (err) => {
                    if (err) console.error('Broadcast error:', err);
                }
            );
        }, this.DISCOVER_INTERVAL);
    }

    // Stop discovery
    stopDiscovery() {
        if (this.discoverySocket) {
            this.discoverySocket.close();
            this.discoverySocket = null;
        }
    }

    // Stop broadcasting
    stopBroadcast() {
        if (this.broadcastInterval) {
            clearInterval(this.broadcastInterval);
            this.broadcastInterval = null;
        }
        if (this.broadcastSocket) {
            this.broadcastSocket.close();
            this.broadcastSocket = null;
        }
    }

    // Cleanup
    stop() {
        this.stopDiscovery();
        this.stopBroadcast();
    }
}

module.exports = NetworkDiscovery;
