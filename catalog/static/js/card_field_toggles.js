document.addEventListener("DOMContentLoaded", function () {
  const supertypeSelect = document.querySelector("#id_supertype");

  if (supertypeSelect) {
    const supertypes = JSON.parse(
      supertypeSelect.getAttribute("data-supertypes"),
    );
    const pokemonFields = document.querySelectorAll(
      ".field-hp, .field-retreat_cost, " +
        ".field-weak_type, .field-weak_value, .field-resist_type, .field-resist_value, " +
        "#abilities-group, #attacks-group",
    );

    const energyFields = document.querySelectorAll(".field-energy_value");

    function toggleFields() {
      const value = supertypeSelect.value;
      const isPokemon = value == supertypes.POKEMON;
      const isEnergy = value == supertypes.ENERGY;
      pokemonFields.forEach((row) => {
        if (row) row.style.display = isPokemon ? "" : "none";
      });
      energyFields.forEach((row) => {
        if (row) row.style.display = isEnergy ? "" : "none";
      });
    }

    supertypeSelect.addEventListener("change", toggleFields);
    toggleFields();
  }
});
