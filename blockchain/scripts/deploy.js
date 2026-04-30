const Web3 = require('web3');
const fs = require('fs');
const path = require('path');
const solc = require('solc');

const GANACHE_URL = process.env.GANACHE_URL || 'http://127.0.0.1:7545';

async function deploy() {
    const web3 = new Web3(new Web3.providers.HttpProvider(GANACHE_URL));
    const accounts = await web3.eth.getAccounts();

    console.log('Deploying from account:', accounts[0]);

    const contractPath = path.resolve(__dirname, '..', 'contracts', 'ElectionResult.sol');
    const source = fs.readFileSync(contractPath, 'utf8');

    const input = {
        language: 'Solidity',
        sources: { 'ElectionResult.sol': { content: source } },
        settings: { outputSelection: { '*': { '*': ['*'] } } }
    };

    const output = JSON.parse(solc.compile(JSON.stringify(input)));
    const compiled = output.contracts['ElectionResult.sol']['ElectionResult'];

    const contract = new web3.eth.Contract(compiled.abi);
    const deployTx = contract.deploy({ data: '0x' + compiled.evm.bytecode.object });
    const gas = await deployTx.estimateGas({ from: accounts[0] });

    const deployed = await deployTx.send({
        from: accounts[0],
        gas: gas + 100000
    });

    console.log('Contract deployed at:', deployed.options.address);

    await deployed.methods.storeResult('test-1', 'abc123hash').send({
        from: accounts[0],
        gas: 200000
    });
    console.log('Test result stored!');

    const result = await deployed.methods.getResult('test-1').call();
    console.log('Retrieved result:', result);

    const verified = await deployed.methods.verifyResult('test-1', 'abc123hash').call();
    console.log('Verification:', verified ? 'PASSED ✅' : 'FAILED ❌');
}

deploy().catch(console.error);
