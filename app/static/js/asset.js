// set up trend log list
var $loglist;
$loglist = $('<div class="mdl-textfield mdl-js-textfield mdl-textfield--floating-label getmdl-select getmdl-select__fix-height">');
var $loglist_input = $('<input class="mdl-textfield__input" type="text" id="loglist" value="" readonly tabIndex="-1">');
var $loglist_label = $('<label for="loglist"><i class="mdl-icon-toggle__label material-icons">keyboard_arrow_down</i></label>')
var $loglist_ul = $('<ul id="loglist_ul" for="loglist" class="mdl-menu mdl-menu--bottom-left mdl-js-menu">');
$loglist.append($loglist_input);
$loglist.append($loglist_label);
$loglist.append($loglist_ul);

// point counter
var point_counter = parseInt($('#initial_points').attr('content')) + 1;

// add a functional descriptor to the list
function addFunction() {
  var function_name = $('#function_list').val();
  var $function_row = $('<tr>');
  var $col = $('<td style="width:250px">');
  $function_row.append($col.clone().append(function_name));
  $function_row.append($col.clone().append('<button type=button onclick="removeFunction(this)">X</button>'));

  // add hidden input to create the actual input
  $function_row.append($('<input type=hidden name="function"/>').val(function_name));

  $('#functional_descriptor_section').append($function_row);
}

// add a point to the list
function addPoint() {
  var point_name = $('#point_list').val();
  var $point_row = $('<tr>');
  var $col = $('<td style="width:250px">');
  $point_row.append($col.clone().append(point_name));
  $loglist_input.attr('name', 'log' + point_counter).attr('id', 'loglist' + point_counter);
  $loglist_label.attr('for', 'loglist' + point_counter);
  $loglist_ul.attr('for', 'loglist' + point_counter);
  $point_row.append($col.clone().append($loglist.clone()));
  $point_row.append($col.clone().append('<button type=button onclick="removePoint(this)">X</button>'));

  // add hidden input to match point name with point trend log
  $point_row.append($('<input type=hidden class="point"/>').val(point_name).attr('name', 'point' + point_counter));

  $('#point_section').append($point_row);

  // re-init the dropdown box
  getmdlSelect.init(".getmdl-select");

  point_counter = point_counter + 1;
}

// remove a functional descriptor from the list
function removeFunction(e) {
  $(e).parent().parent().remove();
}

// remove a point from the list
function removePoint(e) {
  $(e).parent().parent().remove();
}

// generate the list of available trend logs
function buildLogList(type) {
  $.getJSON($('#return_loggedentities').attr('content'), {
    type: type,
  }, function(loglist_data) {
    $.each(loglist_data, function() {
      alert(this);
      $loglist_ul.append($('<li class="mdl-menu__item"/>').attr('data-val', this).text(this));
    })
  });
}

// generate the list of available points for that asset type
function buildPointList(type) {
  $.getJSON($('#return_points').attr('content'), {
    type: type,
  }, function(data) {
    var $point_dropdown = $('#point_list_ul');
    $point_dropdown.html('');
    $.each(data, function() {
      $point_dropdown.append($('<li class="mdl-menu__item"/>').attr('data-val', this).text(this));
    });
    // set initial value
    $('#point_list').val(data[0]);
    // re-init the dropdown box
    getmdlSelect.init(".getmdl-select");
  });
}

// generate the list of available functional descriptors for that asset type
function buildFunctionList(type) {
  $.getJSON($('#return_functions').attr('content'), {
    type: type,
  }, function(data) {
    var $function_dropdown = $('#function_list_ul');
    $function_dropdown.html('');
    $.each(data, function() {
      $function_dropdown.append($('<li class="mdl-menu__item"/>').attr('data-val', this).text(this));
    })
    // set initial value
    $('#function_list').val(data[0]);
    // re-init the dropdown box
    getmdlSelect.init(".getmdl-select");
  });
}

// generate the list of available algorithms for that asset
function buildAlgorithmList(type) {
  $.getJSON($('#return_algorithms').attr('content'), {
    type: type,
  }, function(data) {
    var algorithm_section = $('#algorithm_section');
    algorithm_section.html('');
    $.each(data, function(index) {
      var $algorithm = $('<label class="mdl-checkbox mdl-js-checkbox mdl-js-ripple-effect" for="algorithm' + index + '">');
      var $algorithm_checkbox = $('<input type="checkbox" name="algorithm" id="algorithm' + index + '" class="mdl-checkbox__input" checked>').val(this);
      var $algorithm_label = $('<span class="mdl-checkbox__label">' + this + '</span>');
      $algorithm.append($algorithm_checkbox);
      $algorithm.append($algorithm_label);
      algorithm_section.append($algorithm);
    })
    // upgrade checkboxes
    componentHandler.upgradeAllRegistered()
  });
}

// post uploaded asset data from excel sheet to server for saving
function sendUpload() {
  var assets = {};
  $('.assetrow').each(function(i) {
    assets[i] = {};
    assets[i].name = $(this).find('#name').val();
    assets[i].type = $(this).find('#type').val();
    assets[i].location = $(this).find('#location').val();
    assets[i].group = $(this).find('#group').val();
    assets[i].priority = $(this).find('#priority').val();
  });
  $.post($('#add_asset_confirm').attr('content'), JSON.stringify(assets));
}

// unhide buttons when they become relevant
function unhideButtons() {
  $('#functional_descriptor_add').removeAttr('hidden');
  $('#point_add').removeAttr('hidden');
  $('#submit').removeAttr('hidden');
}

// startup code checks if we are on asset add or edit page
$(function() {
  //check if asset type is pre-defined (edit page)
  if ($('#asset_type').length) {
    var type = $('#asset_type').attr('content');
    buildLogList(type);
    buildPointList(type);
    buildFunctionList(type);
  } else if ($('#type_list').length) {
    // update stuff when a type is selected (add page)
    $('#type_list').change(function() {
      var type = $('#type_list').val();
      buildLogList(type);
      buildPointList(type);
      buildFunctionList(type);
      buildAlgorithmList(type);
      unhideButtons();
      return false;
    });
  }
});
