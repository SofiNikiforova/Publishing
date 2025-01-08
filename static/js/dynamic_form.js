document.addEventListener("DOMContentLoaded", function () {
    const productTypeSelect = document.getElementById("product_type");
    const bookFields = document.getElementById("book_fields");
    const magazineFields = document.getElementById("magazine_fields");
    const advertisementFields = document.getElementById("advertisement_fields");

    const fieldsMap = {
        book: bookFields,
        magazine: magazineFields,
        advertisement: advertisementFields
    };

    // Скрываем все поля по умолчанию
    Object.values(fieldsMap).forEach(field => {
        if (field) field.style.display = "none";
    });

    // Обработчик выбора типа продукции
    productTypeSelect.addEventListener("change", function () {
        const selectedType = productTypeSelect.value;

        // Скрываем все поля
        Object.values(fieldsMap).forEach(field => {
            if (field) field.style.display = "none";
        });

        // Показываем поля выбранного типа
        if (fieldsMap[selectedType]) {
            fieldsMap[selectedType].style.display = "block";
        }
    });
});
