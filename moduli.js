/* Moduli delle pagine dedicate: stesso invio della home (Web3Forms verso commercialetpetrol@gmail.com,
   con email precompilata come riserva). Ogni <form data-oggetto="..."> viene gestito qui. */
(function(){
  var DEST="commercialetpetrol@gmail.com",URL="https://api.web3forms.com/submit",KEY="a8d459e4-7a7b-4ca3-802a-aa838cb086f4";
  document.querySelectorAll("form[data-oggetto]").forEach(function(f){
    var m=f.querySelector(".msg"),btn=f.querySelector("button[type=submit]");
    f.addEventListener("submit",function(e){e.preventDefault();
      var miss=[].slice.call(f.querySelectorAll("[required]")).filter(function(i){return i.type==="checkbox"?!i.checked:!i.value.trim()});
      if(miss.length){m.className="msg";m.textContent="Compila i campi obbligatori: "+miss.map(function(i){return i.type==="checkbox"?"consenso privacy":i.parentElement.firstChild.textContent.replace("*","").trim()}).join(", ")+".";miss[0].focus();return}
      var hp=f.querySelector("[name=_honey]");if(hp&&hp.value)return;
      var fd=Array.from(new FormData(f)).filter(function(p){return p[0]!=="_honey"});
      var luogo=f.querySelector("[name=comune_impianto]");
      var subject=f.dataset.oggetto+(luogo&&luogo.value?" – "+luogo.value:"");
      var body=fd.map(function(p){return p[0].replace(/_/g," ")+": "+p[1]}).join("\n");
      var mailto=function(){m.className="msg";m.textContent="Non siamo riusciti a inviare: si aprirà il tuo programma di posta con la richiesta già compilata. Se non si apre, scrivici a "+DEST+".";
        location.href="mailto:"+DEST+"?subject="+encodeURIComponent(subject)+"&body="+encodeURIComponent(body)};
      var data={access_key:KEY,subject:subject,from_name:"Sito www.tpetrol.it",botcheck:""};
      fd.forEach(function(p){data[p[0].replace(/_/g," ")]=p[1]});
      var em=f.querySelector("[type=email]");if(em&&em.value)data.replyto=em.value;
      btn.disabled=true;m.className="msg";m.textContent="Invio in corso…";
      fetch(URL,{method:"POST",headers:{"Content-Type":"application/json",Accept:"application/json"},body:JSON.stringify(data)})
        .then(function(r){return r.json().catch(function(){return{}}).then(function(j){if(!r.ok||j.success===false||j.success==="false")throw new Error(j.message||r.status)})})
        .then(function(){f.reset();m.className="msg ok";m.textContent="Richiesta inviata, grazie! Ti ricontatteremo al più presto."})
        .catch(mailto).then(function(){btn.disabled=false});
    });
  });
  var y=document.getElementById("yr");if(y)y.textContent=new Date().getFullYear();
})();
