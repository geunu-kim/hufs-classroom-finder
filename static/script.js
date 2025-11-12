document.addEventListener('DOMContentLoaded', () => {
    const resultDisplay = document.getElementById('result');
    const numberButtons = document.querySelectorAll('.number');
    const operatorButtons = document.querySelectorAll('.operator');
    const equalsButton = document.getElementById('equals');
    const clearButton = document.getElementById('clear');
    const deleteButton = document.getElementById('delete');

    let currentInput = '0';
    let operator = null;
    let firstOperand = null;
    let shouldResetDisplay = false;

    function updateDisplay() {
        resultDisplay.value = currentInput;
    }

    function clear() {
        currentInput = '0';
        operator = null;
        firstOperand = null;
        shouldResetDisplay = false;
        updateDisplay();
    }

    function deleteLast() {
        if (currentInput.length > 1) {
            currentInput = currentInput.slice(0, -1);
        } else {
            currentInput = '0';
        }
        updateDisplay();
    }

    function appendNumber(number) {
        if (currentInput === '0' || shouldResetDisplay) {
            currentInput = number;
            shouldResetDisplay = false;
        } else {
            currentInput += number;
        }
        updateDisplay();
    }

    function chooseOperator(op) {
        if (operator !== null && !shouldResetDisplay) {
            calculate();
        }
        firstOperand = parseFloat(currentInput);
        operator = op;
        shouldResetDisplay = true;
    }

    function calculate() {
        if (operator === null || shouldResetDisplay) return;
        const secondOperand = parseFloat(currentInput);
        let result = 0;

        switch (operator) {
            case '+':
                result = firstOperand + secondOperand;
                break;
            case '-':
                result = firstOperand - secondOperand;
                break;
            case '*':
                result = firstOperand * secondOperand;
                break;
            case '/':
                if (secondOperand === 0) {
                    alert("0으로 나눌 수 없습니다.");
                    clear();
                    return;
                }
                result = firstOperand / secondOperand;
                break;
        }
        currentInput = result.toString();
        operator = null;
        firstOperand = null;
        shouldResetDisplay = true;
        updateDisplay();
    }

    numberButtons.forEach(button => {
        button.addEventListener('click', () => {
            appendNumber(button.dataset.num);
        });
    });

    operatorButtons.forEach(button => {
        button.addEventListener('click', () => {
            if (button.dataset.op) {
                chooseOperator(button.dataset.op);
            }
        });
    });

    clearButton.addEventListener('click', clear);
    deleteButton.addEventListener('click', deleteLast);
    equalsButton.addEventListener('click', calculate);
});
