const express = require('express');
const cors = require('cors');
const Web3 = require('web3');
const fs = require('fs');
const path = require('path');
const solc = require('solc');

const app = express();
app.use(cors());
app.use(express.json());

const GANACHE_URL = process.env.GANACHE_URL || 'http://127.0.0.1:7545';
const PORT = process.env.PORT || 3001;

let web3;
let contract;
let contractAddress;
let accounts;

function compileContract() {
    const contractPath = path.resolve(__dirname, 'contracts', 'ElectionResult.sol');
    const source = fs.readFileSync(contractPath, 'utf8');

    const input = {
        language: 'Solidity',
        sources: {
            'ElectionResult.sol': { content: source }
        },
        settings: {
            evmVersion: 'istanbul',
            outputSelection: {
                '*': { '*': ['*'] }
            }
        }
    };

    const output = JSON.parse(solc.compile(JSON.stringify(input)));

    if (output.errors) {
        const errors = output.errors.filter(e => e.severity === 'error');
        if (errors.length > 0) {
            console.error('Compilation errors:', errors);
            throw new Error('Smart contract compilation failed');
        }
    }

    const compiled = output.contracts['ElectionResult.sol']['ElectionResult'];
    return {
        abi: compiled.abi,
        bytecode: compiled.evm.bytecode.object
    };
}

async function deployContract() {
    try {
        web3 = new Web3(new Web3.providers.HttpProvider(GANACHE_URL));
        accounts = await web3.eth.getAccounts();

        if (accounts.length === 0) {
            throw new Error('No accounts found. Is Ganache running?');
        }

        console.log('🔗 Connected to Ganache');
        console.log(`📋 Using account: ${accounts[0]}`);

        const { abi, bytecode } = compileContract();
        console.log('✅ Smart contract compiled successfully');

        const Contract = new web3.eth.Contract(abi);
        const deployTx = Contract.deploy({ data: '0x' + bytecode });

        const gasEstimate = await deployTx.estimateGas({ from: accounts[0] });

        contract = await deployTx.send({
            from: accounts[0],
            gas: gasEstimate + 100000
        });

        contractAddress = contract.options.address;
        console.log(`📄 Contract deployed at: ${contractAddress}`);
        console.log('──────────────────────────────────────');

        return contract;
    } catch (error) {
        console.error('❌ Deployment error:', error.message);
        console.log('⚠️  Make sure Ganache is running on', GANACHE_URL);
        return null;
    }
}

app.get('/api/status', (req, res) => {
    res.json({
        success: true,
        contractDeployed: !!contract,
        contractAddress: contractAddress || null,
        ganacheUrl: GANACHE_URL
    });
});

app.post('/api/store-result', async (req, res) => {
    try {
        if (!contract) {
            return res.json({ success: false, error: 'Smart contract not deployed. Is Ganache running?' });
        }

        const { electionId, resultHash } = req.body;

        if (!electionId || !resultHash) {
            return res.json({ success: false, error: 'electionId and resultHash are required' });
        }

        console.log(`\n📥 Storing result for Election #${electionId}`);
        console.log(`   Hash: ${resultHash}`);

        const tx = await contract.methods
            .storeResult(electionId, resultHash)
            .send({ from: accounts[0], gas: 500000 });

        console.log(`✅ Stored! TX: ${tx.transactionHash}`);

        res.json({
            success: true,
            transactionHash: tx.transactionHash,
            blockNumber: tx.blockNumber,
            contractAddress: contractAddress
        });

    } catch (error) {
        console.error('❌ Store error:', error.message);
        res.json({ success: false, error: error.message });
    }
});

app.get('/api/verify-result/:electionId', async (req, res) => {
    try {
        if (!contract) {
            return res.json({ success: false, error: 'Smart contract not deployed' });
        }

        const { electionId } = req.params;
        const { resultHash } = req.query;

        const isFinalized = await contract.methods.isElectionFinalized(electionId).call();

        if (!isFinalized) {
            return res.json({
                success: true,
                isFinalized: false,
                isVerified: false,
                message: 'Election not finalized on blockchain'
            });
        }

        const storedHash = await contract.methods.getResult(electionId).call();

        let isVerified = false;
        if (resultHash) {
            isVerified = storedHash.toLowerCase() === resultHash.toLowerCase();
        }

        console.log(`\n🔍 Verification for Election #${electionId}`);
        console.log(`   Stored:  ${storedHash}`);
        console.log(`   Given:   ${resultHash || 'N/A'}`);
        console.log(`   Match:   ${isVerified ? '✅ YES' : '❌ NO'}`);

        res.json({
            success: true,
            isFinalized: true,
            storedHash: storedHash,
            isVerified: isVerified,
            electionId: electionId
        });

    } catch (error) {
        console.error('❌ Verify error:', error.message);
        res.json({ success: false, error: error.message });
    }
});

app.get('/api/result/:electionId', async (req, res) => {
    try {
        if (!contract) {
            return res.json({ success: false, error: 'Smart contract not deployed' });
        }

        const { electionId } = req.params;
        const storedHash = await contract.methods.getResult(electionId).call();

        res.json({
            success: true,
            electionId: electionId,
            storedHash: storedHash
        });

    } catch (error) {
        res.json({ success: false, error: error.message });
    }
});

async function start() {
    console.log('╔══════════════════════════════════════════╗');
    console.log('║   Hybrid E-Voting Blockchain Service     ║');
    console.log('╚══════════════════════════════════════════╝');
    console.log('');

    await deployContract();

    app.listen(PORT, () => {
        console.log(`\n🚀 Blockchain service running on http://localhost:${PORT}`);
        console.log(`   Ganache: ${GANACHE_URL}`);
        console.log('   Ready to accept requests!\n');
    });
}

start();
