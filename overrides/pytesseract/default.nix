{config, lib, ...}: {
  deps = {nixpkgs, ...}: {
    inherit (nixpkgs) tesseract;
  };
  mkDerivation.postFixup = ''
    substituteInPlace $out/lib/python*/site-packages/pytesseract/pytesseract.py \
      --replace-fail "tesseract_cmd = 'tesseract'" "tesseract_cmd = '${config.deps.tesseract}/bin/tesseract'"
  '';
}
