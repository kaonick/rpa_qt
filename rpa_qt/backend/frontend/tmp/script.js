// Trigger search when user presses 'Enter'
document.getElementById("searchInput").addEventListener("keyup", function(event) {
    if (event.key === "Enter") {
        searchProduct();
    }
});

// Mock search function
function searchProduct() {
    let query = document.getElementById("searchInput").value;
    console.log("Searching for: " + query);
    // Implement the logic to perform a search and display results
    // For now, it just logs the search query
}

// Open product detail page
function openProductDetailPage() {
    window.location.href = "product-detail.html";  // Change this URL as needed
}
