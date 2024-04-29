function updateFormFields() {
    const subscriptionType = document.getElementById('subscription_type').value;
    const dynamicFields = document.getElementById('dynamic_fields');

    // Clear existing dynamic fields
    dynamicFields.innerHTML = '';

    if (subscriptionType === 'ES') {
        dynamicFields.innerHTML = `
            <li>
                <label for="index">Index:</label>
                <input type="text" id="index" name="index">
            </li>
            <li>
                <label for="query">Query:</label>
                <input type="text" id="query" name="query">
            </li>
        `;
    }
    else if (subscriptionType === 'ORION') {
        dynamicFields.innerHTML = `
            <li>
                <label for="Entity">Entity:</label>
                <input type="text" id="entity" name="entity">
            </li>
            <li>
                <label for="query">Query:</label>
                <input type="text" id="query" name="query">
            </li>
        `;
    }
    else if (subscriptionType === 'Other') {
        dynamicFields.innerHTML = `
            <li>
                <label for="query">Query:</label>
                <input type="text" id="query" name="query">
            </li>
        `;
    }
}

// Ensure form fields are set up correctly when the page loads
document.addEventListener('DOMContentLoaded', function() {
    updateFormFields();
});
