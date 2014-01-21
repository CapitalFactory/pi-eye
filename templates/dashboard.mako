<%inherit file="layout.mako" />

<h1>Dashboard</h1>

<p>This page displays the latest status reported back from each Pi.</p>

%for name, url in image_urls.items():
  <div>
    <h3>${name}</h3>
    <img src="${url}" />
  </div>
%endfor

<script>
// refresh every 10s
setTimeout(function() {
  window.location = window.location;
}, 10000);
</script>
